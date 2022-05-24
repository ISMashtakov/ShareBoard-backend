import uuid

from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import connections

from .exceptions import (
    FileDoesNotExistException
)


class Access(models.IntegerChoices):
    VIEWER = 0
    EDITOR = 1
    OWNER = 2


class FileManager(models.Manager):
    def create(self, **obd_data):
        obd_data['id'] = str(uuid.uuid4())
        return super().create(**obd_data)


class File(models.Model):
    class ProgrammingLanguage(models.TextChoices):
        PYTHON = "python"
        JS = "js"

    id = models.CharField(max_length=128, primary_key=True, db_index=True)
    name = models.CharField(max_length=248)
    programming_language = models.CharField(choices=ProgrammingLanguage.choices, max_length=50)
    content = models.TextField()
    created = models.DateTimeField(default=timezone.now)
    users = models.ManyToManyField(get_user_model(),
                                   through='UserFiles',
                                   related_name='files')

    link_access = models.IntegerField(default=Access.VIEWER, choices=Access.choices)
    last_revision = models.BigIntegerField(default=0)

    objects = FileManager()

    def encode(self):
        return self.id

    @staticmethod
    def decode(data: str):
        try:
            return File.objects.get(id=data)
        except File.DoesNotExist:
            raise FileDoesNotExistException()


def cascade_with_deleting_files_where_user_is_owner(collector, field, sub_objs, using):
    # delete from UserFiles
    collector.collect(
        sub_objs, source=field.remote_field.model, source_attr=field.name,
        nullable=field.null, fail_on_restricted=False,
    )
    if field.null and not connections[using].features.can_defer_constraint_checks:
        collector.add_field_update(field, None, sub_objs)

    # delete from File
    user_files = sub_objs.filter(access=Access.OWNER).all()
    files_for_deleting = File.objects.filter(user_files__in=user_files)

    collector.collect(
        files_for_deleting, source=field.remote_field.model, source_attr=field.name,
        nullable=field.null, fail_on_restricted=False,
    )


class UserFiles(models.Model):
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='user_files')
    user = models.ForeignKey(get_user_model(),
                             on_delete=cascade_with_deleting_files_where_user_is_owner,
                             related_name='user_files')
    access = models.IntegerField(choices=Access.choices)


class Operations(models.Model):
    class Type(models.IntegerChoices):
        NEU = 0
        INSERT = 1
        DELETE = 2

    type = models.IntegerField(choices=Type.choices)
    position = models.IntegerField(blank=True, null=True)
    text = models.TextField(blank=True, null=True)
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='operations')
    revision = models.BigIntegerField()
    channel_name = models.TextField()
