import json

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from authentication.models import CustomUser
from board_manager.models import UserBoards, Board, Access
from board_manager.exceptions import BoardDoesNotExistException
from board_manager.serializers import BoardWithoutContentSerializer


class CreateBoardTestCase(TestCase):

    def setUp(self) -> None:
        self.client = APIClient()

        self.user = CustomUser.objects.create_user(username='Igor Mashtakov',
                                                   email='111@mail.ru',
                                                   password='12345')

        self.client.force_authenticate(user=self.user)

    def tearDown(self) -> None:
        CustomUser.objects.all().delete()
        Board.objects.all().delete()

    def test_authorized_user__create_board(self):
        board_params = {'name': "board_1",
                        'board_type': "kanban"}
        response = self.client.post('/board/create_board/', board_params)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(Board.objects.filter(**board_params).exists())

        board = Board.objects.get(**board_params)
        self.assertTrue(UserBoards.objects.filter(user=self.user, board=board, access=Access.OWNER))

    def test_authorized_user__name_not_given(self):
        response = self.client.post('/board/create_board/', {'board_type': "kanban"})
        self.assertContains(response, "name not given", status_code=status.HTTP_400_BAD_REQUEST)

    def test_authorized_user__bt_not_given(self):
        response = self.client.post('/board/create_board/', {'name': "test_board2"})
        self.assertContains(response, "board_type not given", status_code=status.HTTP_400_BAD_REQUEST)

    def test_save_participants_from_prev_board__two_participant(self):
        board_params = {'name': "board_1",
                        'board_type': "kanban"}
        _ = self.client.post('/board/create_board/', board_params)

        another_client = APIClient()
        another_user = CustomUser.objects.create_user(username='Michael Scofield',
                                                      email='134@mail.ru',
                                                      password='12gh345')
        another_client.force_authenticate(user=another_user)

        board = Board.objects.last()
        UserBoards.objects.create(user=another_user, board=board, access=Access.EDITOR)

        another_board = {'name': "super_board",
                         'board_type': "board_for_notes",
                         'prev_board_id': board.pk}
        response = another_client.post('/board/create_board/', another_board)

        create_board_response = json.loads(response.content)
        self.assertTrue(Board.objects.filter(**create_board_response).exists())

        new_board = Board.objects.get(**create_board_response)
        self.assertTrue(UserBoards.objects.filter(user=self.user, board=new_board, access=Access.EDITOR).exists())
        self.assertTrue(UserBoards.objects.filter(user=another_user, board=new_board, access=Access.OWNER).exists())


class MyBoardsTestCase(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

        self.user = CustomUser.objects.create_user(username='Igor Mashtakov',
                                                   email='111@mail.ru',
                                                   password='12345')

        self.client.force_authenticate(user=self.user)

    def tearDown(self) -> None:
        Board.objects.all().delete()
        CustomUser.objects.all().delete()

    def test_no_boards(self):
        response = self.client.get('/board/my')
        self.assertContains(response, "[]", status_code=status.HTTP_200_OK)

    def test_boards_exist(self):
        board_params = {'name': "board_1",
                        'board_type': "kanban"}
        _ = self.client.post('/board/create_board/', board_params).content
        response = self.client.get('/board/my')

        right_board_data = BoardWithoutContentSerializer(Board.objects.last()).data
        board_data = json.loads(response.content)
        self.assertEqual(len(board_data), 1)
        self.assertDictEqual(board_data[0]['board'], right_board_data)


class DeleteBoardTestsCase(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

        self.user = CustomUser.objects.create_user(username='Igor Mashtakov',
                                                   email='111@mail.ru',
                                                   password='12345')

        self.client.force_authenticate(user=self.user)

    def tearDown(self) -> None:
        Board.objects.all().delete()
        CustomUser.objects.all().delete()

    def test_no_board_id(self):
        response = self.client.post('/board/delete_board/')
        self.assertContains(response, "board_id not given", status_code=status.HTTP_400_BAD_REQUEST)

    def test_no_such_board(self):
        response = self.client.post('/board/delete_board/', {'board_id': 1})
        self.assertContains(response, "Such board does not exist", status_code=status.HTTP_404_NOT_FOUND)

    def test_board_exist(self):
        board_params = {'name': "board_1",
                        'board_type': "kanban"}
        _ = self.client.post('/board/create_board/', board_params)

        response = self.client.post('/board/delete_board/', {'board_id': self.user.boards.get().pk})
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_no_owner(self):
        board_params = {'name': "board_1",
                        'board_type': "kanban"}
        _ = self.client.post('/board/create_board/', board_params)

        another_user = CustomUser.objects.create_user(username='Michael Scolfield',
                                                      email='121@mail.ru',
                                                      password='origami')

        self.client.force_authenticate(user=another_user)

        response = self.client.post('/board/delete_board/', {'board_id': self.user.boards.get().pk})
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
        Board.objects.all().delete()

    def test_no_board_id(self):
        response = self.client.post('/board/open_board/')
        self.assertContains(response, "board_id not given", status_code=status.HTTP_400_BAD_REQUEST)

    def test_board_no_exist(self):
        response = self.client.post('/board/open_board/', {'board_id': 45})
        e = BoardDoesNotExistException()
        self.assertContains(response, e.message, status_code=e.response_status)

    def test_board_exist(self):
        board_params = {'name': "board_1",
                        'board_type': "kanban"}
        _ = self.client.post('/board/create_board/', board_params)

        response = self.client.post('/board/open_board/', {'board_id': self.user.boards.get().pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        encode_content = str(response.content, encoding='UTF-8').split('/')[-1]
        board = Board.decode(encode_content)
        self.assertEqual(board.pk, self.user.boards.get().pk)


class LeaveBoardTestCase(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

        self.user = CustomUser.objects.create_user(username='Igor Mashtakov',
                                                   email='111@mail.ru',
                                                   password='12345')

        self.client.force_authenticate(user=self.user)

        board_params = {'name': "board_1",
                        'board_type': "kanban"}
        _ = self.client.post('/board/create_board/', board_params)
        self.board = Board.objects.last()

    def tearDown(self) -> None:
        Board.objects.all().delete()
        CustomUser.objects.all().delete()

    def test_no_such_board(self):
        response = self.client.post('/board/leave_board/', {'board_id': 'l'})
        self.assertContains(response, 'You must be ANY that to do this', status_code=status.HTTP_406_NOT_ACCEPTABLE)

    def test_owner_leave_board(self):
        response = self.client.post('/board/leave_board/', {'board_id': self.board.pk})
        self.assertContains(response, 'You must be VIEWER OR EDITOR that to do this',
                            status_code=status.HTTP_406_NOT_ACCEPTABLE)

    def test_editor_leave_board(self):
        user_board_relation = UserBoards.objects.get()
        user_board_relation.access = Access.EDITOR
        user_board_relation.save()

        response = self.client.post('/board/leave_board/', {'board_id': self.board.pk})
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
