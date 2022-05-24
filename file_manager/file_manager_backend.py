from .models import File, UserFiles, Access

from .exceptions import (
    NoRequiredFileAccess, FileDoesNotExistException
)


class FileManager:
    @staticmethod
    def create_file(name, programming_language, owner, prev_file_id=None):
        file = File.objects.create(name=name,
                                   programming_language=programming_language)

        UserFiles.objects.create(file=file,
                                 user=owner,
                                 access=Access.OWNER)

        # inherit the user's relationship with the previous file
        if prev_file_id:
            participants = []
            for access_to_file in UserFiles.objects.filter(file__id=prev_file_id).all():
                if access_to_file.user == owner:
                    continue

                access_to_prev_file = access_to_file.access

                if access_to_prev_file == Access.OWNER:
                    access_to_prev_file = Access.EDITOR

                participants.append(UserFiles(user=access_to_file.user, file=file, access=access_to_prev_file))

            UserFiles.objects.bulk_create(participants)
        return file

    @staticmethod
    def delete_file(file_id, user):
        try:
            file = File.objects.get(pk=file_id)

            if not file.user_files.filter(user=user, access=Access.OWNER).exists():
                raise NoRequiredFileAccess('OWNER')

            file.delete()
        except File.DoesNotExist:
            raise FileDoesNotExistException()

    @staticmethod
    def get_user_files(user):
        return UserFiles.objects.filter(user=user).all()

    @staticmethod
    def generate_link(file_id):
        try:
            file = File.objects.get(id=file_id)
            return f"/file/{file.encode()}"
        except File.DoesNotExist:
            raise FileDoesNotExistException()

    @staticmethod
    def leave_file(file_id, user):
        try:
            access_to_file = UserFiles.objects.get(file__id=file_id, user=user)
            if access_to_file.access == Access.OWNER:
                raise NoRequiredFileAccess('VIEWER OR EDITOR')
            access_to_file.delete()

        except UserFiles.DoesNotExist:
            raise NoRequiredFileAccess('ANY')
