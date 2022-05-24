import json

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from authentication.models import CustomUser
from file_manager.models import UserFiles, File, Access
from file_manager.exceptions import FileDoesNotExistException
from file_manager.serializers import FileWithoutContentSerializer


class CreateFileTestCase(TestCase):

    def setUp(self) -> None:
        self.client = APIClient()

        self.user = CustomUser.objects.create_user(username='Igor Mashtakov',
                                                   email='111@mail.ru',
                                                   password='12345')

        self.client.force_authenticate(user=self.user)

    def tearDown(self) -> None:
        CustomUser.objects.all().delete()
        File.objects.all().delete()

    def test_authorized_user__create_file(self):
        file_params = {'name': "file_1",
                       'programming_language': "python"}
        response = self.client.post('/file/create_file/', file_params)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(File.objects.filter(**file_params).exists())

        file = File.objects.get(**file_params)
        self.assertTrue(UserFiles.objects.filter(user=self.user, file=file, access=Access.OWNER))

    def test_authorized_user__filename_not_given(self):
        response = self.client.post('/file/create_file/', {'programming_language': "python"})
        self.assertContains(response, "name not given", status_code=status.HTTP_400_BAD_REQUEST)

    def test_authorized_user__pl_not_given(self):
        response = self.client.post('/file/create_file/', {'name': "test_file2"})
        self.assertContains(response, "programming_language not given", status_code=status.HTTP_400_BAD_REQUEST)

    def test_save_participants_from_prev_file__two_participant(self):
        file_params = {'name': "file_1",
                       'programming_language': "python"}
        _ = self.client.post('/file/create_file/', file_params)

        another_client = APIClient()
        another_user = CustomUser.objects.create_user(username='Michael Scofield',
                                                      email='134@mail.ru',
                                                      password='12gh345')
        another_client.force_authenticate(user=another_user)

        file = File.objects.last()
        UserFiles.objects.create(user=another_user, file=file, access=Access.EDITOR)

        another_file = {'name': "super_file",
                        'programming_language': "js",
                        'prev_file_id': file.pk}
        response = another_client.post('/file/create_file/', another_file)

        create_file_response = json.loads(response.content)
        self.assertTrue(File.objects.filter(**create_file_response).exists())

        new_file = File.objects.get(**create_file_response)
        self.assertTrue(UserFiles.objects.filter(user=self.user, file=new_file, access=Access.EDITOR).exists())
        self.assertTrue(UserFiles.objects.filter(user=another_user, file=new_file, access=Access.OWNER).exists())


class MyFilesTestCase(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

        self.user = CustomUser.objects.create_user(username='Igor Mashtakov',
                                                   email='111@mail.ru',
                                                   password='12345')

        self.client.force_authenticate(user=self.user)

    def tearDown(self) -> None:
        File.objects.all().delete()
        CustomUser.objects.all().delete()

    def test_no_files(self):
        response = self.client.get('/file/my')
        self.assertContains(response, "[]", status_code=status.HTTP_200_OK)

    def test_files_exist(self):
        file_params = {'name': "file_1",
                       'programming_language': "python"}
        _ = self.client.post('/file/create_file/', file_params).content
        response = self.client.get('/file/my')

        right_file_data = FileWithoutContentSerializer(File.objects.last()).data
        file_data = json.loads(response.content)
        self.assertEqual(len(file_data), 1)
        self.assertDictEqual(file_data[0]['file'], right_file_data)


class DeleteFileTestsCase(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

        self.user = CustomUser.objects.create_user(username='Igor Mashtakov',
                                                   email='111@mail.ru',
                                                   password='12345')

        self.client.force_authenticate(user=self.user)

    def tearDown(self) -> None:
        File.objects.all().delete()
        CustomUser.objects.all().delete()

    def test_no_file_id(self):
        response = self.client.post('/file/delete_file/')
        self.assertContains(response, "file_id not given", status_code=status.HTTP_400_BAD_REQUEST)

    def test_no_such_file(self):
        response = self.client.post('/file/delete_file/', {'file_id': 1})
        self.assertContains(response, "Such file does not exist", status_code=status.HTTP_404_NOT_FOUND)

    def test_file_exist(self):
        file_params = {'name': "file_1",
                       'programming_language': "python"}
        _ = self.client.post('/file/create_file/', file_params)

        response = self.client.post('/file/delete_file/', {'file_id': self.user.files.get().pk})
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_no_owner(self):
        file_params = {'name': "file_1",
                       'programming_language': "python"}
        _ = self.client.post('/file/create_file/', file_params)

        another_user = CustomUser.objects.create_user(username='Michael Scolfield',
                                                      email='121@mail.ru',
                                                      password='origami')

        self.client.force_authenticate(user=another_user)

        response = self.client.post('/file/delete_file/', {'file_id': self.user.files.get().pk})
        self.assertContains(response, "You must be OWNER that to do this", status_code=status.HTTP_406_NOT_ACCEPTABLE)


class GenerateLinkTestCase(TestCase):

    def setUp(self) -> None:
        self.client = APIClient()

        self.user = CustomUser.objects.create_user(username='Igor Mashtakov',
                                                   email='111@mail.ru',
                                                   password='12345')

        self.client.force_authenticate(user=self.user)

    def tearDown(self) -> None:
        CustomUser.objects.all().delete()
        File.objects.all().delete()

    def test_no_file_id(self):
        response = self.client.post('/file/open_file/')
        self.assertContains(response, "file_id not given", status_code=status.HTTP_400_BAD_REQUEST)

    def test_file_no_exist(self):
        response = self.client.post('/file/open_file/', {'file_id': 45})
        e = FileDoesNotExistException()
        self.assertContains(response, e.message, status_code=e.response_status)

    def test_file_exist(self):
        file_params = {'name': "file_1",
                       'programming_language': "python"}
        _ = self.client.post('/file/create_file/', file_params)

        response = self.client.post('/file/open_file/', {'file_id': self.user.files.get().pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        encode_content = str(response.content, encoding='UTF-8').split('/')[-1]
        file = File.decode(encode_content)
        self.assertEqual(file.pk, self.user.files.get().pk)


class LeaveFileTestCase(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

        self.user = CustomUser.objects.create_user(username='Igor Mashtakov',
                                                   email='111@mail.ru',
                                                   password='12345')

        self.client.force_authenticate(user=self.user)

        file_params = {'name': "file_1",
                       'programming_language': "python"}
        _ = self.client.post('/file/create_file/', file_params)
        self.file = File.objects.last()

    def tearDown(self) -> None:
        File.objects.all().delete()
        CustomUser.objects.all().delete()

    def test_no_such_file(self):
        response = self.client.post('/file/leave_file/', {'file_id': 'l'})
        self.assertContains(response, 'You must be ANY that to do this', status_code=status.HTTP_406_NOT_ACCEPTABLE)

    def test_owner_leave_file(self):
        response = self.client.post('/file/leave_file/', {'file_id': self.file.pk})
        self.assertContains(response, 'You must be VIEWER OR EDITOR that to do this',
                            status_code=status.HTTP_406_NOT_ACCEPTABLE)

    def test_editor_leave_file(self):
        user_file_relation = UserFiles.objects.get()
        user_file_relation.access = Access.EDITOR
        user_file_relation.save()

        response = self.client.post('/file/leave_file/', {'file_id': self.file.pk})
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
