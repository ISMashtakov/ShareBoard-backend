from rest_framework import serializers

from board_manager.models import Board, UserBoards, Node
from authentication.serializers import UserSerializer


class BoardWithoutContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Board
        exclude = ['users']
        

class UserBoardsSerializer(serializers.ModelSerializer):
    board = BoardWithoutContentSerializer(read_only=True)

    class Meta:
        model = UserBoards
        exclude = ('id', 'user')


class UserWithAccessSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = UserBoards
        fields = ('user', 'access')


class BoardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Board
        fields = ('id', 'name', 'board_type', 'link_access')


class NodeSerializer(serializers.ModelSerializer):
    full_tag = serializers.SerializerMethodField('get_full_tag')

    def get_full_tag(self, node: Node):
        return str(node.board.prefix) + '-' + str(node.tag)

    class Meta:
        model = Node
        exclude = ['tag']

