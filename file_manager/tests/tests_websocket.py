from unittest.mock import patch
import json

from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase
from channels_presence.models import Presence
from asgiref.sync import sync_to_async

from CodeDocs_backend.asgi import application
from authentication.models import CustomUser
from file_manager.models import File, UserFiles, Access, Operations
from file_manager.file_manager_backend import FileManager
from authentication.serializers import UserSerializer
from file_manager.serializers import (
    FileSerializer, UserWithAccessSerializer, OperationSerializer
)


class MockJWTTokenUserAuthentication:
    @staticmethod
    def get_validated_token(*args):
        return 1

    @staticmethod
    def get_user(*args):
        try:
            return CustomUser.objects.last()
        except Exception as e:
            print(e)


class FileEditorConsumerTestCase(TransactionTestCase):

    def setUp(self) -> None:
        self.user = CustomUser.objects.create_user(username='Igor Mashtakov',
                                                   email='111@mail.ru',
                                                   password='12345')
        self.file = FileManager.create_file(name="file_1", programming_language="python", owner=self.user)
        self.file = self.user.files.get()

        self.token_patcher = patch('rest_framework_simplejwt.authentication.JWTAuthentication.get_validated_token',
                                   MockJWTTokenUserAuthentication.get_validated_token)
        self.token_patcher.start()

        self.user_patcher = patch('rest_framework_simplejwt.authentication.JWTTokenUserAuthentication.get_user',
                                  MockJWTTokenUserAuthentication.get_user)
        self.user_patcher.start()

    def tearDown(self) -> None:
        File.objects.all().delete()
        CustomUser.objects.all().delete()

        self.token_patcher.stop()
        self.user_patcher.stop()

    async def test_connection__file_does_not_exist(self):
        communicator = WebsocketCommunicator(application.application_mapping["websocket"],
                                             "/files/yuyu/1278/")
        await communicator.connect()

        answer = await communicator.output_queue.get()
        self.assertEqual(answer, {'type': 'websocket.close', 'code': 4404})

    async def test_connection__user_have_not_access_to_file(self):
        def delete_user_file_relation():
            user_file_relation = UserFiles.objects.last()
            user_file_relation.access = Access.EDITOR
            user_file_relation.save()

            UserFiles.objects.all().delete()

        await sync_to_async(delete_user_file_relation)()

        # user without access to file
        communicator = WebsocketCommunicator(application.application_mapping["websocket"],
                                             f"/files/{self.file.pk}/1278/")
        await communicator.connect()

        # channel_name
        channel_name_answer = await communicator.output_queue.get()
        self.assertEqual(channel_name_answer['type'], 'websocket.send')

        channel_name_json = json.loads(channel_name_answer['text'])
        channel_name = (await sync_to_async(Presence.objects.get)(user=self.user)).channel_name
        right_channel_name_json = {'type': "channel_name",
                                   'channel_name': channel_name}
        self.assertDictEqual(channel_name_json, right_channel_name_json)

        # file status
        file_status_answer = await communicator.output_queue.get()
        file_status_json = json.loads(file_status_answer['text'])
        right_file_status_json = {'type': 'file_status',
                                  'is_running': False}
        self.assertDictEqual(file_status_json, right_file_status_json)

        # user without access to file
        new_user_answer = await communicator.output_queue.get()
        default_access = (await sync_to_async(File.objects.get)(id=self.file.pk)).link_access
        answer = json.loads(new_user_answer['text'])
        right_answer = {'type': 'new_user',
                        'user': {
                            'user': UserSerializer(self.user).data,
                            'access': default_access
                        }}
        self.assertDictEqual(answer, right_answer)

    async def test_connection__one_connection(self):
        communicator = WebsocketCommunicator(application.application_mapping["websocket"],
                                             f"/files/{self.file.pk}/1278/")
        await communicator.connect()

        # channel_name
        channel_name_answer = await communicator.output_queue.get()
        channel_name_json = json.loads(channel_name_answer['text'])
        channel_name = (await sync_to_async(Presence.objects.get)(user=self.user)).channel_name
        right_channel_name_json = {'type': "channel_name",
                                   'channel_name': channel_name}
        self.assertDictEqual(channel_name_json, right_channel_name_json)

        # file status
        file_status_answer = await communicator.output_queue.get()
        file_status_json = json.loads(file_status_answer['text'])
        right_file_status_json = {'type': 'file_status',
                                  'is_running': False}
        self.assertDictEqual(file_status_json, right_file_status_json)

        # new user
        new_user_answer = await communicator.output_queue.get()
        answer = json.loads(new_user_answer['text'])
        right_answer = {'type': 'new_user',
                        'user': {
                            'user': UserSerializer(self.user).data,
                            'access': Access.OWNER
                        }}
        self.assertDictEqual(answer, right_answer)

    async def test_connection__two_connections_from_one_user(self):
        # the first connection
        communicator = WebsocketCommunicator(application.application_mapping["websocket"],
                                             f"/files/{self.file.pk}/1278/")
        await communicator.connect()

        # channel_name
        channel_name_answer = await communicator.output_queue.get()
        channel_name_json = json.loads(channel_name_answer['text'])
        channel_name = (await sync_to_async(Presence.objects.get)(user=self.user)).channel_name
        right_channel_name_json = {'type': "channel_name",
                                   'channel_name': channel_name}
        self.assertDictEqual(channel_name_json, right_channel_name_json)

        # file status
        file_status_answer = await communicator.output_queue.get()
        file_status_json = json.loads(file_status_answer['text'])
        right_file_status_json = {'type': 'file_status',
                                  'is_running': False}
        self.assertDictEqual(file_status_json, right_file_status_json)

        # new_user
        new_user_answer = await communicator.output_queue.get()
        answer = json.loads(new_user_answer['text'])
        right_answer = {'type': 'new_user',
                        'user': {
                            'user': UserSerializer(self.user).data,
                            'access': Access.OWNER
                        }}
        self.assertDictEqual(answer, right_answer)

        # the second connection
        another_communicator = WebsocketCommunicator(application.application_mapping["websocket"],
                                                     f"/files/{self.file.pk}/1278/")
        await another_communicator.connect()

        # another channel_name
        another_channel_name_answer = await another_communicator.output_queue.get()
        another_channel_name_json = json.loads(another_channel_name_answer['text'])

        def get_last_presence():
            return Presence.objects.filter(user=self.user).last().channel_name
        another_channel_name = await sync_to_async(get_last_presence)()
        right_another_channel_name_json = {'type': "channel_name",
                                           'channel_name': another_channel_name}
        self.assertDictEqual(another_channel_name_json, right_another_channel_name_json)

        # file status
        file_status_answer = await another_communicator.output_queue.get()
        file_status_json = json.loads(file_status_answer['text'])
        right_file_status_json = {'type': 'file_status',
                                  'is_running': False}
        self.assertDictEqual(file_status_json, right_file_status_json)

        # no new user answer
        self.assertTrue(await another_communicator.receive_nothing(1))
        self.assertEqual(2, await sync_to_async(Presence.objects.count)())  # number of connections

    async def test_file_info(self):
        communicator = WebsocketCommunicator(application.application_mapping["websocket"],
                                             f"/files/{self.file.pk}/1278/")
        await communicator.connect()

        _ = await communicator.output_queue.get()  # channel_name
        _ = await communicator.output_queue.get()  # file_status
        _ = await communicator.output_queue.get()  # new_user

        await communicator.send_json_to({'type': 'file_info'})
        file_info_answer = await communicator.output_queue.get()
        self.assertEqual(file_info_answer['type'], 'websocket.send')

        file_answer = json.loads(file_info_answer['text'])
        right_file_answer = {'type': 'file_info',
                             'file': FileSerializer(self.file).data}
        self.assertDictEqual(file_answer, right_file_answer)

    async def test_active_users__one_user(self):
        communicator = WebsocketCommunicator(application.application_mapping["websocket"],
                                             f"/files/{self.file.pk}/1278/")
        await communicator.connect()

        _ = await communicator.output_queue.get()  # channel_name
        _ = await communicator.output_queue.get()  # file_status
        _ = await communicator.output_queue.get()  # new_user

        await communicator.send_json_to({'type': 'active_users'})

        active_users_answer = await communicator.output_queue.get()
        users_answer = json.loads(active_users_answer['text'])

        def access_to_file():
            users_with_access = UserFiles.objects.filter(user=self.user, file=self.file).all()
            return UserWithAccessSerializer(users_with_access, many=True).data

        right_users_answer = {'type': 'active_users',
                              'users': await sync_to_async(access_to_file)()}
        self.assertDictEqual(users_answer, right_users_answer)

    async def test_active_users__users(self):
        # the first user connect
        communicator = WebsocketCommunicator(application.application_mapping["websocket"],
                                             f"/files/{self.file.pk}/1278/")
        await communicator.connect()

        _ = await communicator.output_queue.get()  # channel_name
        _ = await communicator.output_queue.get()  # file_status
        _ = await communicator.output_queue.get()  # new_user

        users_data = [{'username': 'Michael', 'email': '1@mail.ru', 'password': '1345'},
                      {'username': 'Shon', 'email': 'd@merfi.com', 'password': 'surgeon'}]

        # connect other users
        for user_data in users_data:
            _ = await sync_to_async(CustomUser.objects.create_user)(**user_data)

            another_communicator = WebsocketCommunicator(application.application_mapping["websocket"],
                                                         f"/files/{self.file.pk}/1278/")
            await another_communicator.connect()
            _ = await communicator.output_queue.get()  # new user

        await communicator.send_json_to({'type': 'active_users'})
        active_users_answer = await communicator.output_queue.get()
        users_answer = json.loads(active_users_answer['text'])

        def check_active_users():
            users = UserFiles.objects.all()
            serialized_users = UserWithAccessSerializer(users, many=True).data
            self.assertTrue(len(serialized_users), len(users_answer['users']))
            for user in serialized_users:
                self.assertTrue(user in users_answer['users'])

        await sync_to_async(check_active_users)()

    async def test_active_users__two_connections_from_one_user(self):
        # the first connection
        communicator = WebsocketCommunicator(application.application_mapping["websocket"],
                                             f"/files/{self.file.pk}/1278/")
        await communicator.connect()

        _ = await communicator.output_queue.get()  # channel_name
        _ = await communicator.output_queue.get()  # file_status
        _ = await communicator.output_queue.get()  # new_user

        # the second connection
        another_communicator = WebsocketCommunicator(application.application_mapping["websocket"],
                                                     f"/files/{self.file.pk}/1278/")
        await another_communicator.connect()

        _ = await another_communicator.output_queue.get()  # channel_name
        _ = await another_communicator.output_queue.get()  # file_status

        # active users
        await communicator.send_json_to({'type': 'active_users'})

        active_users_answer = await communicator.output_queue.get()
        users_answer = json.loads(active_users_answer['text'])

        def access_to_file():
            users_with_access = UserFiles.objects.filter(user=self.user, file=self.file).all()
            return UserWithAccessSerializer(users_with_access, many=True).data

        right_users_answer = {'type': 'active_users',
                              'users': await sync_to_async(access_to_file)()}
        self.assertDictEqual(users_answer, right_users_answer)

        self.assertEqual(2, await sync_to_async(Presence.objects.count)())  # number of connections

    async def test_all_users__one_user(self):
        communicator = WebsocketCommunicator(application.application_mapping["websocket"],
                                             f"/files/{self.file.pk}/1278/")
        await communicator.connect()

        _ = await communicator.output_queue.get()  # channel_name
        _ = await communicator.output_queue.get()  # file_status
        _ = await communicator.output_queue.get()  # new_user

        await communicator.send_json_to({'type': 'all_users'})

        all_users_answer = await communicator.output_queue.get()
        users_answer = json.loads(all_users_answer['text'])

        def access_to_file():
            users_with_access = UserFiles.objects.filter(user=self.user, file=self.file).all()
            return UserWithAccessSerializer(users_with_access, many=True).data

        right_users_answer = {'type': 'all_users',
                              'users': await sync_to_async(access_to_file)()}
        self.assertDictEqual(users_answer, right_users_answer)

    async def test_all_users__two_connections_from_one_user(self):
        # the first connection
        communicator = WebsocketCommunicator(application.application_mapping["websocket"],
                                             f"/files/{self.file.pk}/1278/")
        await communicator.connect()

        _ = await communicator.output_queue.get()  # channel_name
        _ = await communicator.output_queue.get()  # file_status
        _ = await communicator.output_queue.get()  # new_user

        # the second connection
        another_communicator = WebsocketCommunicator(application.application_mapping["websocket"],
                                                     f"/files/{self.file.pk}/1278/")
        await another_communicator.connect()

        _ = await another_communicator.output_queue.get()  # channel_name
        _ = await another_communicator.output_queue.get()  # file_status

        # active users
        await communicator.send_json_to({'type': 'all_users'})

        all_users_answer = await communicator.output_queue.get()
        users_answer = json.loads(all_users_answer['text'])

        def access_to_file():
            users_with_access = UserFiles.objects.filter(user=self.user, file=self.file).all()
            return UserWithAccessSerializer(users_with_access, many=True).data

        right_users_answer = {'type': 'all_users',
                              'users': await sync_to_async(access_to_file)()}
        self.assertDictEqual(users_answer, right_users_answer)

        self.assertEqual(2, await sync_to_async(Presence.objects.count)())  # number of connections

    async def test_all_users__several_users(self):
        # the first user connect
        communicator = WebsocketCommunicator(application.application_mapping["websocket"],
                                             f"/files/{self.file.pk}/1278/")
        await communicator.connect()

        _ = await communicator.output_queue.get()  # channel_name
        _ = await communicator.output_queue.get()  # file_status
        _ = await communicator.output_queue.get()  # new_user

        users_data = [{'username': 'Michael', 'email': '1@mail.ru', 'password': '1345'},
                      {'username': 'Shon', 'email': 'd@merfi.com', 'password': 'surgeon'}]

        # connect other users
        for user_data in users_data:
            _ = await sync_to_async(CustomUser.objects.create_user)(**user_data)

        await communicator.send_json_to({'type': 'all_users'})
        all_users_answer = await communicator.output_queue.get()
        users_answer = json.loads(all_users_answer['text'])

        def serialized_all_users():
            users = UserFiles.objects.all()
            return UserWithAccessSerializer(users, many=True).data

        right_users_answer = {'type': "all_users",
                              'users': await sync_to_async(serialized_all_users)()}
        self.assertDictEqual(users_answer, right_users_answer)

    async def test_change_file_config__change_filename(self):
        communicator = WebsocketCommunicator(application.application_mapping["websocket"],
                                             f"/files/{self.file.pk}/1278/")
        await communicator.connect()

        _ = await communicator.output_queue.get()  # channel_name
        _ = await communicator.output_queue.get()  # file_status
        _ = await communicator.output_queue.get()  # new_user

        new_name = 'another_file_1'
        await communicator.send_json_to({'type': 'change_file_config',
                                         'config': {
                                             'name': new_name
                                         }})
        self.file.name = new_name

        file_info_answer = await communicator.output_queue.get()
        file_answer = json.loads(file_info_answer['text'])
        right_file_answer = {'type': 'change_file_config',
                             'file': FileSerializer(self.file).data}
        self.assertDictEqual(file_answer, right_file_answer)

    async def test_change_file_config__change_filename_and_pl(self):
        communicator = WebsocketCommunicator(application.application_mapping["websocket"],
                                             f"/files/{self.file.pk}/1278/")
        await communicator.connect()

        _ = await communicator.output_queue.get()  # channel_name
        _ = await communicator.output_queue.get()  # file_status
        _ = await communicator.output_queue.get()  # new_user

        new_file_config = {'name': 'another_file_1',
                           'programming_language': 'js'}
        await communicator.send_json_to({'type': 'change_file_config',
                                         'config': new_file_config})

        self.file.name = new_file_config['name']
        self.file.programming_language = new_file_config['programming_language']

        file_info_answer = await communicator.output_queue.get()
        file_answer = json.loads(file_info_answer['text'])
        right_file_answer = {'type': 'change_file_config',
                             'file': FileSerializer(self.file).data}
        self.assertDictEqual(file_answer, right_file_answer)

    async def test_change_file_config__change_to_the_same_config(self):
        communicator = WebsocketCommunicator(application.application_mapping["websocket"],
                                             f"/files/{self.file.pk}/1278/")
        await communicator.connect()

        _ = await communicator.output_queue.get()  # channel_name
        _ = await communicator.output_queue.get()  # file_status
        _ = await communicator.output_queue.get()  # new_user

        new_file_config = {'name': self.file.name,
                           'programming_language': self.file.programming_language}
        await communicator.send_json_to({'type': 'change_file_config',
                                         'config': new_file_config})

        file_info_answer = await communicator.output_queue.get()
        file_answer = json.loads(file_info_answer['text'])
        right_file_answer = {'type': 'change_file_config',
                             'file': FileSerializer(self.file).data}
        self.assertDictEqual(file_answer, right_file_answer)

    async def test_change_file_config__change_nothing(self):
        communicator = WebsocketCommunicator(application.application_mapping["websocket"],
                                             f"/files/{self.file.pk}/1278/")
        await communicator.connect()

        _ = await communicator.output_queue.get()  # channel_name
        _ = await communicator.output_queue.get()  # file_status
        _ = await communicator.output_queue.get()  # new_user

        await communicator.send_json_to({'type': 'change_file_config',
                                         'config': {}})
        file_info_answer = await communicator.output_queue.get()

        file_answer = json.loads(file_info_answer['text'])
        right_file_answer = {'type': 'change_file_config',
                             'file': FileSerializer(self.file).data}
        self.assertDictEqual(file_answer, right_file_answer)

    async def test_change_link_access(self):
        communicator = WebsocketCommunicator(application.application_mapping["websocket"],
                                             f"/files/{self.file.pk}/1278/")
        await communicator.connect()

        _ = await communicator.output_queue.get()  # channel_name
        _ = await communicator.output_queue.get()  # file_status
        _ = await communicator.output_queue.get()  # new_user

        new_access = Access.EDITOR
        await communicator.send_json_to({'type': 'change_link_access',
                                         'new_access': new_access})

        file_info_answer = await communicator.output_queue.get()
        file_answer = json.loads(file_info_answer['text'])
        right_file_answer = {'type': 'change_link_access',
                             'new_access': new_access}
        self.assertDictEqual(file_answer, right_file_answer)

        await sync_to_async(self.file.refresh_from_db)()
        self.assertEqual(self.file.link_access, new_access)

    async def test_change_user_access__cannot_change_user_access(self):
        # the first user connect
        communicator = WebsocketCommunicator(application.application_mapping["websocket"],
                                             f"/files/{self.file.pk}/1278/")
        await communicator.connect()

        _ = await communicator.output_queue.get()  # channel_name
        _ = await communicator.output_queue.get()  # file_status
        _ = await communicator.output_queue.get()  # new_user

        # the second user connect
        _ = await sync_to_async(CustomUser.objects.create_user)(username='Michael Scofield',
                                                                email='1@mail.ru',
                                                                password='15')
        another_communicator = WebsocketCommunicator(application.application_mapping["websocket"],
                                                     f"/files/{self.file.pk}/1278/")
        await another_communicator.connect()

        _ = await another_communicator.output_queue.get()  # channel_name
        _ = await another_communicator.output_queue.get()  # file_status
        _ = await another_communicator.output_queue.get()  # new_user

        # the second user try to change the first user access
        await another_communicator.send_json_to({'type': 'change_user_access',
                                                 'new_access': Access.EDITOR,
                                                 'another_user_id': self.user.pk})

        change_user_access_answer = await another_communicator.output_queue.get()
        change_access_answer = json.loads(change_user_access_answer['text'])
        right_change_access_answer = {'type': 'change_user_access',
                                      'error_code': 4403,
                                      'message': ''}
        self.assertDictEqual(change_access_answer, right_change_access_answer)

    async def test_change_user_access__cannot_change_to_this_access(self):
        def change_access():
            access_to_file = UserFiles.objects.get(user=self.user, file=self.file)
            access_to_file.access = Access.VIEWER
            access_to_file.save()

        await sync_to_async(change_access)()

        # the first user connect
        communicator = WebsocketCommunicator(application.application_mapping["websocket"],
                                             f"/files/{self.file.pk}/1278/")
        await communicator.connect()

        _ = await communicator.output_queue.get()  # channel_name
        _ = await communicator.output_queue.get()  # file_status
        _ = await communicator.output_queue.get()  # new_user

        # the second user connect
        _ = await sync_to_async(CustomUser.objects.create_user)(username='Michael Scofield',
                                                                email='1@mail.ru',
                                                                password='15')
        another_communicator = WebsocketCommunicator(application.application_mapping["websocket"],
                                                     f"/files/{self.file.pk}/1278/")
        await another_communicator.connect()

        _ = await another_communicator.output_queue.get()  # channel_name
        _ = await another_communicator.output_queue.get()  # file_status
        _ = await another_communicator.output_queue.get()  # new_user

        # the second user try to change the first user access
        await another_communicator.send_json_to({'type': 'change_user_access',
                                                 'new_access': Access.EDITOR,
                                                 'another_user_id': self.user.pk})

        change_user_access_answer = await another_communicator.output_queue.get()
        change_access_answer = json.loads(change_user_access_answer['text'])
        right_change_access_answer = {'type': 'change_user_access',
                                      'error_code': 4406,
                                      'message': ''}
        self.assertDictEqual(change_access_answer, right_change_access_answer)

    async def test_change_user_access__oks(self):
        # the first user connect
        communicator = WebsocketCommunicator(application.application_mapping["websocket"],
                                             f"/files/{self.file.pk}/1278/")
        await communicator.connect()

        _ = await communicator.output_queue.get()  # channel_name
        _ = await communicator.output_queue.get()  # file_status
        _ = await communicator.output_queue.get()  # new_user

        # the second user connect
        another_user = await sync_to_async(CustomUser.objects.create_user)(username='Michael Scofield',
                                                                           email='1@mail.ru',
                                                                           password='15')
        another_communicator = WebsocketCommunicator(application.application_mapping["websocket"],
                                                     f"/files/{self.file.pk}/1278/")
        await another_communicator.connect()

        _ = await another_communicator.output_queue.get()  # channel_name
        _ = await another_communicator.output_queue.get()  # file_status
        _ = await another_communicator.output_queue.get()  # new_user

        await communicator.send_json_to({'type': 'change_user_access',
                                         'new_access': Access.EDITOR,
                                         'another_user_id': another_user.pk})

        change_user_access_answer = await another_communicator.output_queue.get()
        change_access_answer = json.loads(change_user_access_answer['text'])

        def another_user_with_access():
            user_with_access = UserFiles.objects.get(user=another_user, file=self.file)
            return UserWithAccessSerializer(user_with_access).data
        right_change_access_answer = {'type': 'change_user_access',
                                      'user': await sync_to_async(another_user_with_access)()}
        self.assertDictEqual(change_access_answer, right_change_access_answer)

    async def test_apply_operation__one_operation(self):
        communicator = WebsocketCommunicator(application.application_mapping["websocket"],
                                             f"/files/{self.file.pk}/1278/")
        await communicator.connect()

        _ = await communicator.output_queue.get()  # channel_name
        _ = await communicator.output_queue.get()  # file_status
        _ = await communicator.output_queue.get()  # new_user

        operation = {'type': Operations.Type.INSERT,
                     'position': 0,
                     'text': "Hello!"}
        await communicator.send_json_to({'type': 'apply_operation',
                                         'revision': 0,
                                         'operation': operation})

        apply_operation_answer = await communicator.output_queue.get()

        def check_operation():
            prev_revision = self.file.last_revision
            self.file.refresh_from_db()
            self.assertEqual(prev_revision + 1, self.file.last_revision)
            self.assertEqual(self.file.content, operation['text'])

            self.assertTrue(Operations.objects.filter(**operation, revision=self.file.last_revision).exists())

            operation_answer = json.loads(apply_operation_answer['text'])

            db_operation = Operations.objects.last()
            right_operation_answer = {'type': 'apply_operation',
                                      'operation': OperationSerializer(db_operation).data}
            self.assertDictEqual(operation_answer, right_operation_answer)

        await sync_to_async(check_operation)()

    async def test_apply_operation__several_operations(self):
        # the first connect
        communicator = WebsocketCommunicator(application.application_mapping["websocket"],
                                             f"/files/{self.file.pk}/1278/")
        await communicator.connect()

        _ = await communicator.output_queue.get()  # channel_name
        _ = await communicator.output_queue.get()  # file_status
        _ = await communicator.output_queue.get()  # new_user

        self.file.link_access = Access.EDITOR
        await sync_to_async(self.file.save)()

        # the second_connect
        _ = await sync_to_async(CustomUser.objects.create_user)(username='Michael Scofield',
                                                                email='1@mail.ru',
                                                                password='15')
        another_communicator = WebsocketCommunicator(application.application_mapping["websocket"],
                                                     f"/files/{self.file.pk}/1278/")
        await another_communicator.connect()

        _ = await another_communicator.output_queue.get()  # channel_name
        _ = await another_communicator.output_queue.get()  # file_status
        _ = await another_communicator.output_queue.get()  # new_user
        _ = await communicator.output_queue.get()  # new_user

        operation1 = {'type': Operations.Type.INSERT,
                      'position': 0,
                      'text': "Hello!"}
        operation2 = {'type': Operations.Type.INSERT,
                      'position': 5,
                      'text': " World!"}
        operation3 = {'type': Operations.Type.DELETE,
                      'position': 0,
                      'text': "He"}
        operation4 = {'type': Operations.Type.NEU,
                      'position': None,
                      'text': None}

        # send operations
        await communicator.send_json_to({'type': 'apply_operation',
                                         'revision': 0,
                                         'operation': operation1})
        self.assertDictEqual(await communicator.output_queue.get(), await another_communicator.output_queue.get())

        await communicator.send_json_to({'type': 'apply_operation',
                                         'revision': 1,
                                         'operation': operation4})
        self.assertDictEqual(await communicator.output_queue.get(), await another_communicator.output_queue.get())

        await another_communicator.send_json_to({'type': 'apply_operation',
                                                 'revision': 2,
                                                 'operation': operation3})
        self.assertDictEqual(await communicator.output_queue.get(), await another_communicator.output_queue.get())

        await communicator.send_json_to({'type': 'apply_operation',
                                         'revision': 2,
                                         'operation': operation2})
        self.assertDictEqual(await communicator.output_queue.get(), await another_communicator.output_queue.get())

        def check_result():
            self.file.refresh_from_db()
            self.assertEqual(self.file.last_revision, 4)
            self.assertEqual(self.file.content, "llo World!!")

            self.assertTrue(Operations.objects.count(), 4)

        await sync_to_async(check_result)()

    async def test_apply_operation__owner_and_viewer(self):
        # the first connect
        communicator = WebsocketCommunicator(application.application_mapping["websocket"],
                                             f"/files/{self.file.pk}/1278/")
        await communicator.connect()

        _ = await communicator.output_queue.get()  # channel_name
        _ = await communicator.output_queue.get()  # file_status
        _ = await communicator.output_queue.get()  # new_user

        # the second_connect
        _ = await sync_to_async(CustomUser.objects.create_user)(username='Michael Scofield',
                                                                email='1@mail.ru',
                                                                password='15')
        another_communicator = WebsocketCommunicator(application.application_mapping["websocket"],
                                                     f"/files/{self.file.pk}/1278/")
        await another_communicator.connect()

        _ = await another_communicator.output_queue.get()  # channel_name
        _ = await another_communicator.output_queue.get()  # file_status
        _ = await another_communicator.output_queue.get()  # new_user
        _ = await communicator.output_queue.get()  # new_user

        operation1 = {'type': Operations.Type.INSERT,
                      'position': 0,
                      'text': "Hello!"}
        operation2 = {'type': Operations.Type.INSERT,
                      'position': 5,
                      'text': " World!"}
        operation3 = {'type': Operations.Type.DELETE,
                      'position': 0,
                      'text': "He"}
        operation4 = {'type': Operations.Type.NEU,
                      'position': None,
                      'text': None}

        # send operations
        await communicator.send_json_to({'type': 'apply_operation',
                                         'revision': 0,
                                         'operation': operation1})
        self.assertDictEqual(await communicator.output_queue.get(), await another_communicator.output_queue.get())

        await communicator.send_json_to({'type': 'apply_operation',
                                         'revision': 1,
                                         'operation': operation4})
        self.assertDictEqual(await communicator.output_queue.get(), await another_communicator.output_queue.get())

        await another_communicator.send_json_to({'type': 'apply_operation',
                                                 'revision': 2,
                                                 'operation': operation3})
        self.assertTrue(await another_communicator.receive_nothing(1))
        self.assertTrue(await communicator.receive_nothing(1))

        await communicator.send_json_to({'type': 'apply_operation',
                                         'revision': 3,
                                         'operation': operation2})
        self.assertDictEqual(await communicator.output_queue.get(), await another_communicator.output_queue.get())

        def check_result():
            self.file.refresh_from_db()
            self.assertEqual(self.file.last_revision, 3)
            self.assertEqual(self.file.content, "Hello World!!")

            self.assertTrue(Operations.objects.count(), 3)

        await sync_to_async(check_result)()

    async def test_change_cursor_position(self):
        # the first connection
        communicator = WebsocketCommunicator(application.application_mapping["websocket"],
                                             f"/files/{self.file.pk}/1278/")
        await communicator.connect()

        _ = await communicator.output_queue.get()  # channel_name
        _ = await communicator.output_queue.get()  # file_status
        _ = await communicator.output_queue.get()  # new_user

        # the second_connect
        _ = await sync_to_async(CustomUser.objects.create_user)(username='Michael Scofield',
                                                                email='1@mail.ru',
                                                                password='15')
        another_communicator = WebsocketCommunicator(application.application_mapping["websocket"],
                                                     f"/files/{self.file.pk}/1278/")
        await another_communicator.connect()

        _ = await another_communicator.output_queue.get()  # channel_name
        _ = await another_communicator.output_queue.get()  # file_status
        _ = await another_communicator.output_queue.get()  # new_user
        _ = await communicator.output_queue.get()  # new_user

        dispatch = {'type': 'change_cursor_position',
                    'position': 12}
        await communicator.send_json_to(dispatch)

        change_cursor_position_answer = await another_communicator.output_queue.get()
        change_cursor_answer = json.loads(change_cursor_position_answer['text'])
        right_cursor_answer = {**dispatch,
                               'user_id': self.user.pk}
        self.assertDictEqual(change_cursor_answer, right_cursor_answer)
