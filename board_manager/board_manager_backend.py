import random
import string

from .models import Board, UserBoards, Access, Column

from .exceptions import (
    NoRequiredBoardAccess, BoardDoesNotExistException
)


class BoardManager:
    @staticmethod
    def create_board(name, board_type, owner, prev_board_id=None):
        board = Board.objects.create(name=name,
                                     board_type=board_type,
                                     prefix=''.join(random.choices(string.ascii_lowercase, k=5)))

        UserBoards.objects.create(board=board,
                                  user=owner,
                                  access=Access.OWNER)

        # inherit the user's relationship with the previous board
        if prev_board_id:
            participants = []
            for access_to_board in UserBoards.objects.filter(board__id=prev_board_id).all():
                if access_to_board.user == owner:
                    continue

                access_to_prev_board = access_to_board.access

                if access_to_prev_board == Access.OWNER:
                    access_to_prev_board = Access.EDITOR

                participants.append(UserBoards(user=access_to_board.user, board=board, access=access_to_prev_board))

            UserBoards.objects.bulk_create(participants)

        if board_type == Board.BoardTypes.KANBAN:
            Column.objects.create(board=board, name='TODO', position=0)
            Column.objects.create(board=board, name='IN PROGRESS', position=1)
            Column.objects.create(board=board, name='DONE', position=2)
        return board

    @staticmethod
    def delete_board(board_id, user):
        try:
            board = Board.objects.get(pk=board_id)

            if not board.user_boards.filter(user=user, access=Access.OWNER).exists():
                raise NoRequiredBoardAccess('OWNER')

            board.delete()
        except Board.DoesNotExist:
            raise BoardDoesNotExistException()

    @staticmethod
    def get_user_boards(user):
        return UserBoards.objects.filter(user=user).all()

    @staticmethod
    def generate_link(board_id):
        try:
            board = Board.objects.get(id=board_id)
            return f"/board/{board.encode()}"
        except Board.DoesNotExist:
            raise BoardDoesNotExistException()

    @staticmethod
    def leave_board(board_id, user):
        try:
            access_to_board = UserBoards.objects.get(board__id=board_id, user=user)
            if access_to_board.access == Access.OWNER:
                raise NoRequiredBoardAccess('VIEWER OR EDITOR')
            access_to_board.delete()

        except UserBoards.DoesNotExist:
            raise NoRequiredBoardAccess('ANY')
