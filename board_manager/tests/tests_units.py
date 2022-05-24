from django.test import TestCase

from board_manager.exceptions import (
    BoardDoesNotExistException, NoRequiredBoardAccess
)
from board_manager.board_manager_backend import BoardManager
from authentication.models import CustomUser
from board_manager.models import UserBoards, Board, Access


class CreateBoardTestCase(TestCase):
    def setUp(self) -> None:
        self.user = CustomUser.objects.create_user(username='Igor Mashtakov',
                                                   email='masht@mail.ru',
                                                   password='12345')

    def tearDown(self) -> None:
        Board.objects.all().delete()

    def test_create_board(self):
        board = BoardManager.create_board(name="board_1", board_type="kanban", owner=self.user)

        self.assertTrue(UserBoards.objects.filter(board=board,
                                                  user=self.user,
                                                  access=Access.OWNER).exists())


class DeleteBoardTestCase(TestCase):
    def setUp(self) -> None:
        self.user = CustomUser.objects.create_user(username='Igor Mashtakov',
                                                   email='masht@mail.ru',
                                                   password='12345')

    def tearDown(self) -> None:
        Board.objects.all().delete()

    def test_delete_board(self):
        board = BoardManager.create_board(name="board_1", board_type="kanban", owner=self.user)

        BoardManager.delete_board(board_id=board.pk, user=self.user)

        self.assertFalse(UserBoards.objects.filter(board=board.pk,
                                                   user=self.user.pk,
                                                   access=Access.OWNER).exists())

    def test_no_such_board(self):
        with self.assertRaises(BoardDoesNotExistException):
            BoardManager.delete_board(board_id=-1, user=self.user)

    def test_no_owner(self):
        board = BoardManager.create_board(name="board_1", board_type="kanban", owner=self.user)

        another_user = CustomUser.objects.create_user(username='Michael Scolfield',
                                                      email='121@mail.ru',
                                                      password='origami')

        with self.assertRaises(NoRequiredBoardAccess):
            BoardManager.delete_board(board_id=board.pk, user=another_user)


class MyBoardsTestCase(TestCase):
    def setUp(self) -> None:
        self.user = CustomUser.objects.create_user(username='Igor Mashtakov',
                                                   email='masht@mail.ru',
                                                   password='12345')

    def tearDown(self) -> None:
        Board.objects.all().delete()

    def test_no_boards(self):
        boards = BoardManager.get_user_boards(self.user)
        self.assertEqual(boards.count(), 0)

    def test_boards_exist(self):
        board = BoardManager.create_board(name="board_1", board_type="kanban", owner=self.user)

        boards = BoardManager.get_user_boards(self.user)
        self.assertTrue(boards.filter(board=board).exists())


class GenerateLinkTestCase(TestCase):
    def setUp(self) -> None:
        self.user = CustomUser.objects.create_user(username='Igor Mashtakov',
                                                   email='masht@mail.ru',
                                                   password='12345')

    def tearDown(self) -> None:
        Board.objects.all().delete()

    def test_board_no_exist(self):
        with self.assertRaises(BoardDoesNotExistException):
            BoardManager.generate_link(-1)

    def test_board_exist(self):
        board = BoardManager.create_board(name="board_1", board_type="kanban", owner=self.user)
        result = BoardManager.generate_link(board.pk)

        encode_board = result.split('/')[-1]

        decode_board = Board.decode(encode_board)
        self.assertEqual(board, decode_board)
