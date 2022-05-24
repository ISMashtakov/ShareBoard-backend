class Operation:
    def __init__(self, position, text):
        self.start = position
        self.text = text

    def __truediv__(self, prev_operation):
        pass

    def execute(self, file_content):
        pass

    def __str__(self):
        return f"[{self.__class__}, {self.start} {self.text}]"

    @property
    def end(self):
        return self.start + len(self.text)

    def info(self):
        pass


class NeutralOperation(Operation):
    def __init__(self):
        super().__init__(None, None)

    def execute(self, file_content):
        return file_content

    def __truediv__(self, prev_operation):
        return NeutralOperation()

    def info(self):
        return {'type': 0}


class Insert(Operation):
    def execute(self, file_content):
        return file_content[:self.start] + self.text + file_content[self.start:]

    def __truediv__(self, prev_operation):
        # prev_operation - insert
        if isinstance(prev_operation, Insert):
            if self.start <= prev_operation.start:
                return Insert(self.start, self.text)
            else:
                return Insert(self.start + len(prev_operation.text), self.text)
        # prev_operation - delete
        elif isinstance(prev_operation, Delete):
            if self.start <= prev_operation.start:
                return Insert(self.start, self.text)
            elif self.start > prev_operation.end:
                return Insert(self.start - len(prev_operation.text), self.text)
            else:
                return Insert(prev_operation.start, self.text)
        # prev_operation - neu
        elif isinstance(prev_operation, NeutralOperation):
            return Insert(self.start, self.text)

    def info(self):
        return {'type': 1,
                'position': self.start,
                'text': self.text}


class Delete(Operation):
    def execute(self, file_content):
        return file_content[:self.start] + file_content[self.start + len(self.text):]

    def __truediv__(self, prev_operation):
        # prev_operation - insert
        if isinstance(prev_operation, Insert):
            if prev_operation.start <= self.start:
                return Delete(self.start + len(prev_operation.text), self.text)
            elif self.start < prev_operation.start < self.end:
                difference = prev_operation.start - self.start
                return Delete(self.start, self.text[:difference] + prev_operation.text + self.text[difference:])
            else:
                return Delete(self.start, self.text)
        # prev_operation - delete
        elif isinstance(prev_operation, Delete):
            if self.end <= prev_operation.start:
                return Delete(self.start, self.text)

            elif (self.start < prev_operation.start) and (prev_operation.start < self.end <= prev_operation.end):
                return Delete(self.start, self.text[:prev_operation.start - self.start])

            elif (prev_operation.start <= self.start) and (self.end <= prev_operation.end):
                return NeutralOperation()

            elif (prev_operation.start <= self.start <= prev_operation.end) and (prev_operation.end < self.end):
                return Delete(prev_operation.start, self.text[prev_operation.end - self.start:])

            elif self.start > prev_operation.end:
                return Delete(self.start - len(prev_operation.text), self.text)

            else:
                return Delete(self.start, self.text[:prev_operation.start - self.start] +
                              self.text[prev_operation.end - self.start:])
        # prev_operation - neu
        elif isinstance(prev_operation, NeutralOperation):
            return Delete(self.start, self.text)

    def info(self):
        return {'type': 2,
                'position': self.start,
                'text': self.text}
