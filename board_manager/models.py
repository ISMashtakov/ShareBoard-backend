import uuid

from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import connections

from .exceptions import (
    BoardDoesNotExistException
)


class Access(models.IntegerChoices):
    VIEWER = 0
    EDITOR = 1
    OWNER = 2


class BoardManager(models.Manager):
    def create(self, **obd_data):
        obd_data['id'] = str(uuid.uuid4())
        return super().create(**obd_data)


class Board(models.Model):
    class BoardTypes(models.TextChoices):
        KANBAN = "kanban"
        BOARD_FOR_NOTES = "board_for_notes"

    id = models.CharField(max_length=128, primary_key=True, db_index=True)
    name = models.CharField(max_length=248)
    board_type = models.CharField(choices=BoardTypes.choices, max_length=50)
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(default=timezone.now)
    users = models.ManyToManyField(get_user_model(),
                                   through='UserBoards',
                                   related_name='boards')
    prefix = models.CharField(max_length=8)

    link_access = models.IntegerField(default=Access.VIEWER, choices=Access.choices)

    objects = BoardManager()

    def encode(self):
        return self.id

    @staticmethod
    def decode(data: str):
        try:
            return Board.objects.get(id=data)
        except Board.DoesNotExist:
            raise BoardDoesNotExistException()


def cascade_with_deleting_boards_where_user_is_owner(collector, field, sub_objs, using):
    # delete from UserBoards
    collector.collect(
        sub_objs, source=field.remote_field.model, source_attr=field.name,
        nullable=field.null, fail_on_restricted=False,
    )
    if field.null and not connections[using].features.can_defer_constraint_checks:
        collector.add_field_update(field, None, sub_objs)

    # delete from board
    user_boards = sub_objs.filter(access=Access.OWNER).all()
    boards_for_deleting = Board.objects.filter(user_boards__in=user_boards)

    collector.collect(
        boards_for_deleting, source=field.remote_field.model, source_attr=field.name,
        nullable=field.null, fail_on_restricted=False,
    )


class UserBoards(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='user_boards')
    user = models.ForeignKey(get_user_model(),
                             on_delete=cascade_with_deleting_boards_where_user_is_owner,
                             related_name='user_boards')
    access = models.IntegerField(choices=Access.choices)


class Node(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='nodes')
    title = models.CharField(max_length=248, default='Untitled')
    description = models.TextField(default='')
    tag = models.IntegerField()
    link_to = models.CharField(max_length=248, default='')
    status = models.CharField(max_length=248, null=True, default=None)
    color = models.CharField(max_length=16)
    assigned = models.CharField(max_length=248, null=True, default=None)
    position_x = models.FloatField(default=100)
    position_y = models.FloatField(default=100)
    blocked_by = models.ForeignKey(get_user_model(), related_name='blocked_nodes',
                                   on_delete=models.SET_NULL, null=True, default=None)
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(default=timezone.now)

    @staticmethod
    def create(board: Board, tag: str, color: str) -> Node:
        return Node.objects.create(board=board, tag=tag, color=color)

    def can_be_changed(self, field: str) -> bool:
        return field in ['title', 'description', 'link_to', 'status', 'assigned', 'position_x', 'position_y']
