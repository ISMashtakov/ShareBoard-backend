from .models import Operations
from .operations import NeutralOperation, Insert, Delete


class OperationFactory:
    operations = {
        Operations.Type.NEU: lambda *_: NeutralOperation(),
        Operations.Type.INSERT: lambda position, text: Insert(position, text),
        Operations.Type.DELETE: lambda position, text: Delete(position, text)
    }

    @staticmethod
    def create(type_operation, position, text):
        return OperationFactory.operations[type_operation](position, text)
