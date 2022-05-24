from rest_framework import serializers

from file_manager.models import File, UserFiles, Operations
from authentication.serializers import UserSerializer


class FileWithoutContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        exclude = ('created', 'users', 'content')


class UserFilesSerializer(serializers.ModelSerializer):
    file = FileWithoutContentSerializer(read_only=True)

    class Meta:
        model = UserFiles
        exclude = ('id', 'user')


class UserWithAccessSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = UserFiles
        fields = ('user', 'access')


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ('id', 'name', 'programming_language', 'content', 'link_access', 'last_revision')


class OperationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Operations
        fields = ('type', 'position', 'text', 'revision', 'channel_name')
