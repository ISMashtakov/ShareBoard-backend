from django.test import TestCase

from file_manager.exceptions import (
    FileDoesNotExistException, NoRequiredFileAccess
)
from file_manager.file_manager_backend import FileManager
from authentication.models import CustomUser
from file_manager.models import UserFiles, File, Access


class CreateFileTestCase(TestCase):
    def setUp(self) -> None:
        self.user = CustomUser.objects.create_user(username='Igor Mashtakov',
                                                   email='masht@mail.ru',
                                                   password='12345')

    def tearDown(self) -> None:
        File.objects.all().delete()

    def test_create_file(self):
        file = FileManager.create_file(name="file_1", programming_language="python", owner=self.user)

        self.assertTrue(UserFiles.objects.filter(file=file,
                                                 user=self.user,
                                                 access=Access.OWNER).exists())


class DeleteFileTestCase(TestCase):
    def setUp(self) -> None:
        self.user = CustomUser.objects.create_user(username='Igor Mashtakov',
                                                   email='masht@mail.ru',
                                                   password='12345')

    def tearDown(self) -> None:
        File.objects.all().delete()

    def test_delete_file(self):
        file = FileManager.create_file(name="file_1", programming_language="python", owner=self.user)

        FileManager.delete_file(file_id=file.pk, user=self.user)

        self.assertFalse(UserFiles.objects.filter(file=file.pk,
                                                  user=self.user.pk,
                                                  access=Access.OWNER).exists())

    def test_no_such_file(self):
        with self.assertRaises(FileDoesNotExistException):
            FileManager.delete_file(file_id=-1, user=self.user)

    def test_no_owner(self):
        file = FileManager.create_file(name="file_1", programming_language="python", owner=self.user)

        another_user = CustomUser.objects.create_user(username='Michael Scolfield',
                                                      email='121@mail.ru',
                                                      password='origami')

        with self.assertRaises(NoRequiredFileAccess):
            FileManager.delete_file(file_id=file.pk, user=another_user)


class MyFilesTestCase(TestCase):
    def setUp(self) -> None:
        self.user = CustomUser.objects.create_user(username='Igor Mashtakov',
                                                   email='masht@mail.ru',
                                                   password='12345')

    def tearDown(self) -> None:
        File.objects.all().delete()

    def test_no_files(self):
        files = FileManager.get_user_files(self.user)
        self.assertEqual(files.count(), 0)

    def test_files_exist(self):
        file = FileManager.create_file(name="file_1", programming_language="python", owner=self.user)

        files = FileManager.get_user_files(self.user)
        self.assertTrue(files.filter(file=file).exists())


class GenerateLinkTestCase(TestCase):
    def setUp(self) -> None:
        self.user = CustomUser.objects.create_user(username='Igor Mashtakov',
                                                   email='masht@mail.ru',
                                                   password='12345')

    def tearDown(self) -> None:
        File.objects.all().delete()

    def test_file_no_exist(self):
        with self.assertRaises(FileDoesNotExistException):
            FileManager.generate_link(-1)

    def test_file_exist(self):
        file = FileManager.create_file(name="file_1", programming_language="python", owner=self.user)
        result = FileManager.generate_link(file.pk)

        encode_file = result.split('/')[-1]

        decode_file = File.decode(encode_file)
        self.assertEqual(file, decode_file)
