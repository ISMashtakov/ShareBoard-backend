import datetime
import json

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

from authentication.account_colors import random_color
from authentication.models import CustomUser
from .models import Board, UserBoards, Node
from .serializers import (
    UserWithAccessSerializer,
    BoardSerializer, NodeSerializer
)
from authentication.serializers import UserSerializer
from .exceptions import BoardManagerException
from .catch_websocket_exceptions import catch_websocket_exception


class BoardEditorConsumer(JsonWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_group_name = None
        self.room = None
        self.board = None

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

        # get board
        try:
            self.board = Board.decode(self.scope['url_route']['kwargs']['boards_id'])
        except BoardManagerException as e:
            self.close_connection(e.response_status)

        self.room_group_name = f"board_{self.board.pk}"

        # check access to board
        try:
            access_to_board = UserBoards.objects.get(user=self.scope['user'], board=self.board)
        except UserBoards.DoesNotExist:
            access_to_board = UserBoards.objects.create(user=self.scope['user'],
                                                        board=self.board,
                                                        access=self.board.link_access)

        # Join room group
        async_to_sync(self.channel_layer.group_add)(self.room_group_name,
                                                    self.channel_name)
        self.room = Room.objects.add(self.room_group_name, self.channel_name, self.scope["user"])

        user_serializer = UserWithAccessSerializer(access_to_board)

        self.send_json({'type': 'channel_name',
                        'channel_name': self.channel_name})

        self.send_json({'type': 'current_user',
                        'user': user_serializer.data})

        self.send_json({'type': 'board_info',
                        'board': BoardSerializer(self.board).data})

        if Presence.objects.filter(user=self.scope['user'], room=self.room).count() == 1:
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
    def active_users(self, event):
        users = self.room.get_users()
        users_with_accesses = UserBoards.objects.filter(user__in=users, board=self.board).all()
        serializer = UserWithAccessSerializer(users_with_accesses, many=True)
        self.send_json({**event,
                        'users': serializer.data})

    @catch_websocket_exception([])
    def all_users(self, event):
        all_users = UserBoards.objects.filter(board=self.board).all()
        serializer = UserWithAccessSerializer(all_users, many=True)
        self.send_json({**event,
                        'users': serializer.data})

    @catch_websocket_exception(['new_access'])
    def change_link_access(self, event):
        self.board.refresh_from_db()
        self.board.link_access = event['new_access']
        self.board.updated = datetime.datetime.now()
        self.board.save()
        self.send_to_group(event)

    @catch_websocket_exception(['another_user_id', 'new_access'])
    def change_user_access(self, event):
        another_user = UserBoards.objects.get(user__id=event['another_user_id'], board=self.board)

        current_user_access = UserBoards.objects.get(user=self.scope['user'], board=self.board).access
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

    @catch_websocket_exception([])
    def board_info(self, event):
        self.board.refresh_from_db()
        board_serializer = BoardSerializer(self.board)
        self.send_json({**event,
                        'board': board_serializer.data})

    @catch_websocket_exception(['config'])
    def change_board_config(self, event):
        self.board.refresh_from_db()
        for field in event['config']:
            setattr(self.board, field, event['config'][field])
        self.board.updated = datetime.datetime.now()
        self.board.save()

        board_serializer = BoardSerializer(self.board)
        self.send_to_group({'type': event['type'],
                            'board': board_serializer.data})

    def send_change_node(self, node: Node):
        self.send_to_group({'type': "node_changed",
                            'node': NodeSerializer(node).data})

    @catch_websocket_exception([])
    def board_nodes(self, event):
        self.send_json({'type': 'board_nodes',
                        'nodes': NodeSerializer(self.board.nodes.all(), many=True).data})

    @catch_websocket_exception(['node_id'])
    def start_changing_node(self, event):
        try:
            node = Node.objects.get(id=event['node_id'])
        except Node.DoesNotExist:
            return
        if node.blocked_by is not None:
            self.send_json({'type': "can_not_changing",
                            'node': NodeSerializer(node).data})
            return
        node.blocked_by = self.scope['user']
        node.save()
        self.send_change_node(node)

    @catch_websocket_exception(['node'])
    def changing_node(self, event):
        try:
            node = Node.objects.get(id=event['node']['id'])
        except Node.DoesNotExist:
            return

        if node.blocked_by != self.scope['user']:
            self.send_json({'type': "can_not_changing",
                            'node': NodeSerializer(node).data})
            return

        for field in event['node']:
            if node.can_be_changed(field):
                setattr(node, field, event['node'][field])
        node.updated = datetime.datetime.now()
        node.save()

        self.board.refresh_from_db()
        self.board.updated = datetime.datetime.now()
        self.board.save()

        self.send_change_node(node)

    @catch_websocket_exception(['node_id'])
    def stop_changing_node(self, event):
        try:
            node = Node.objects.get(id=event['node_id'])
        except Node.DoesNotExist:
            return
        if node.blocked_by != self.scope['user']:
            self.send_json({'type': "can_not_changing",
                            'node': NodeSerializer(node).data})
            return
        node.blocked_by = None
        node.save()
        self.send_change_node(node)

    @catch_websocket_exception([])
    def create_node(self, event):
        self.board.refresh_from_db()
        self.board.updated = datetime.datetime.now()
        self.board.save()
        nodes = Node.objects.filter(board=self.board).order_by('-tag').all()
        if len(nodes) == 0:
            max_tag = 0
        else:
            max_tag = nodes[0].tag
        node = Node.create(self.board, tag=max_tag+1, color=random_color())

        self.send_to_group({'type': "node_created",
                            'node': NodeSerializer(node).data})

    @catch_websocket_exception(['node_id'])
    def delete_node(self, event):
        try:
            node = Node.objects.get(id=event['node_id'])
        except Node.DoesNotExist:
            return
        if node.blocked_by != self.scope['user']:
            self.send_json({'type': "can_not_changing",
                            'node': NodeSerializer(node).data})
            return
        node_id = node.pk
        node.delete()

        self.board.refresh_from_db()
        self.board.updated = datetime.datetime.now()
        self.board.save()

        self.send_to_group({"type": "node_deleted",
                            "node_id" : node_id
                            })

    @remove_presence
    def disconnect(self, code):
        # leave room
        if not Presence.objects.filter(user=self.scope['user'], room=self.room).exists():
            self.send_to_group({'type': 'delete_user',
                                'user_id': self.scope['user'].pk})
            blocked_nodes = Node.objects.filter(board=self.board, blocked_by=self.scope['user']).all()
            for node in blocked_nodes:
                node.blocked_by = None
                node.save()
                self.send_change_node(node)

        async_to_sync(self.channel_layer.group_discard)(self.room_group_name,
                                                        self.channel_name)
