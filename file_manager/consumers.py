from channels.generic.websocket import JsonWebsocketConsumer
from asgiref.sync import async_to_sync
from rest_framework_simplejwt.authentication import JWTTokenUserAuthentication
from channels_presence.models import Room, Presence
from channels_presence.decorators import (
    remove_presence, touch_presence
)
from rest_framework_simplejwt.exceptions import InvalidToken
from channels.exceptions import StopConsumer
from rest_framework import status

from authentication.models import CustomUser
from .models import File, UserFiles, Operations, Access
from .serializers import (
    UserWithAccessSerializer, FileSerializer, OperationSerializer
)
from authentication.serializers import UserSerializer
from .exceptions import FileManageException
from .operation_factory import OperationFactory as Factory
from .run_file import RunFileThread
from .launched_files import LaunchedFilesManager
from .catch_websocket_exceptions import catch_websocket_exception


class FileEditorConsumer(JsonWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file = None
        self.room_group_name = None
        self.room = None
        self.launched_file_manager = LaunchedFilesManager()
        self.file_output_index = 0

    def connect(self):
        self.accept()

        # get current user
        try:
            jwt = JWTTokenUserAuthentication()
            validated_token = jwt.get_validated_token(self.scope['url_route']['kwargs']['access_token'])
            token_user = jwt.get_user(validated_token)
            self.scope['user'] = CustomUser.objects.get(pk=token_user.pk)
        except InvalidToken as e:
            self.close_connection(e.status_code)

        if not self.scope['user'].is_authenticated:
            self.close_connection(status.HTTP_401_UNAUTHORIZED)

        # get file
        try:
            self.file = File.decode(self.scope['url_route']['kwargs']['file_id'])
        except FileManageException as e:
            self.close_connection(e.response_status)

        self.room_group_name = f"file_{self.file.pk}"

        # check access to file
        try:
            access_to_file = UserFiles.objects.get(user=self.scope['user'], file=self.file)
        except UserFiles.DoesNotExist:
            access_to_file = UserFiles.objects.create(user=self.scope['user'],
                                                      file=self.file,
                                                      access=self.file.link_access)

        # Join room group
        async_to_sync(self.channel_layer.group_add)(self.room_group_name,
                                                    self.channel_name)
        self.room = Room.objects.add(self.room_group_name, self.channel_name, self.scope["user"])

        self.send_json({'type': 'channel_name',
                        'channel_name': self.channel_name})

        self.send_json({'type': 'file_status',
                        'is_running': self.launched_file_manager.file_is_running(self.file.pk)})

        if Presence.objects.filter(user=self.scope['user'], room=self.room).count() == 1:
            user_serializer = UserWithAccessSerializer(access_to_file)
            self.send_to_group({'type': 'new_user',
                                'user': user_serializer.data})

    def close_connection(self, http_code):
        self.close(4000 + http_code)
        raise StopConsumer()

    def send_content(self, content):
        self.send_json(content['content'])

    def send_to_group(self, content):
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, {'type': 'send_content',
                                   'content': content})

    def send_error(self, package_type, error_code, message=""):
        self.send_json({"type": package_type,
                        "error_code": 4000 + error_code,
                        "message": message})

    @touch_presence
    def receive_json(self, content, **kwargs):
        getattr(self, content['type'])(content)

    @catch_websocket_exception([])
    def file_info(self, event):
        self.file.refresh_from_db()
        file_serializer = FileSerializer(self.file)
        self.send_json({**event,
                        'file': file_serializer.data})

    @catch_websocket_exception([])
    def active_users(self, event):
        users = self.room.get_users()
        users_with_accesses = UserFiles.objects.filter(user__in=users, file=self.file).all()
        serializer = UserWithAccessSerializer(users_with_accesses, many=True)
        self.send_json({**event,
                        'users': serializer.data})

    @catch_websocket_exception([])
    def all_users(self, event):
        all_users = UserFiles.objects.filter(file=self.file).all()
        serializer = UserWithAccessSerializer(all_users, many=True)
        self.send_json({**event,
                        'users': serializer.data})

    @catch_websocket_exception(['config'])
    def change_file_config(self, event):
        self.file.refresh_from_db()
        for field in event['config']:
            setattr(self.file, field, event['config'][field])

        self.file.save()

        file_serializer = FileSerializer(self.file)
        self.send_to_group({'type': event['type'],
                            'file': file_serializer.data})

    @catch_websocket_exception(['new_access'])
    def change_link_access(self, event):
        self.file.refresh_from_db()
        self.file.link_access = event['new_access']
        self.file.save()
        self.send_to_group(event)

    @catch_websocket_exception(['another_user_id', 'new_access'])
    def change_user_access(self, event):
        another_user = UserFiles.objects.get(user__id=event['another_user_id'], file=self.file)

        current_user_access = UserFiles.objects.get(user=self.scope['user'], file=self.file).access
        if current_user_access < another_user.access:
            self.send_error(event['type'], status.HTTP_403_FORBIDDEN)
        elif current_user_access < event['new_access']:
            self.send_error(event['type'], status.HTTP_406_NOT_ACCEPTABLE)
        else:
            another_user.access = event['new_access']
            another_user.save()

            user_serializer = UserWithAccessSerializer(another_user)
            self.send_to_group({'type': event['type'],
                                'user': user_serializer.data})

    @catch_websocket_exception(['revision', 'operation'])
    def apply_operation(self, event):
        current_user_access = UserFiles.objects.get(user=self.scope['user'], file=self.file).access
        if current_user_access == Access.VIEWER:
            return

        bd_operations = Operations.objects.filter(revision__gt=event['revision'],
                                                  file=self.file).order_by('revision').all()
        operations = [Factory.create(operation.type, operation.position, operation.text) for operation in bd_operations]

        # operation transformation
        current_operation = Factory.create(event['operation']['type'],
                                           event['operation']['position'],
                                           event['operation']['text'])
        for operation in operations:
            current_operation /= operation

        # update file content
        self.file.refresh_from_db()
        self.file.content = current_operation.execute(self.file.content)
        self.file.last_revision += 1
        self.file.save()

        current_operation_query = Operations.objects.create(**current_operation.info(),
                                                            revision=self.file.last_revision,
                                                            file=self.file,
                                                            channel_name=self.channel_name)

        operation_serializer = OperationSerializer(current_operation_query)
        self.send_to_group({'type': event['type'],
                            'operation': operation_serializer.data})

    @catch_websocket_exception(['revision'])
    def operation_history(self, event):
        operations_query = Operations.objects.filter(revision__gt=event['revision']).order_by('revision').all()

        operation_serializer = OperationSerializer(operations_query, many=True)
        self.send_json({'type': event['type'],
                        'operations': operation_serializer.data})

    @catch_websocket_exception(['position'])
    def change_cursor_position(self, event):
        self.send_to_group({**event,
                            'user_id': self.scope['user'].pk})

    @catch_websocket_exception([])
    def run_file(self, event):
        self.file.refresh_from_db()

        if self.launched_file_manager.file_is_running(file_id=self.file.pk):
            self.send_error(event['type'], status.HTTP_409_CONFLICT)
        else:
            # create RunFilThread when the file is not running
            my_thread = RunFileThread(self.file.pk, self.file.content, self.file.programming_language, self)
            try:
                self.launched_file_manager.add_running_file(self.file.pk, my_thread)

                self.send_to_group({"type": "START run_file"})
                my_thread.start()
            except FileManageException as e:
                self.send_error(event['type'], e.response_status)

    def file_output(self, file_output):
        self.send_to_group({'type': 'file_output',
                            'file_output': file_output,
                            'index': self.file_output_index})
        self.file_output_index += 1

    @catch_websocket_exception(['file_input'])
    def file_input(self, event):
        self.launched_file_manager.get_thread_by_file_id(self.file.pk).add_input(event['file_input'])

    @catch_websocket_exception([])
    def stop_file(self, event):
        try:
            file_thread = self.launched_file_manager.get_thread_by_file_id(self.file.pk)
            file_thread.close()

            self.launched_file_manager.remove_stopped_file(self.file.pk)
            self.file_output_index = 0
        except FileManageException as e:
            self.send_error(event['type'], e.response_status)

    @remove_presence
    def disconnect(self, code):
        # leave room
        if not Presence.objects.filter(user=self.scope['user'], room=self.room).exists():
            user_serializer = UserSerializer(self.scope['user'])
            self.send_to_group({'type': 'delete_user',
                                'user': user_serializer.data})

        # last connection
        if not self.room.get_users().exists():
            Operations.objects.filter(file=self.file).all().delete()
            self.file.last_revision = 0
            self.file.save()

        async_to_sync(self.channel_layer.group_discard)(self.room_group_name,
                                                        self.channel_name)
