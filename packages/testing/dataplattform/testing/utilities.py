class FakeResponse:
    status: int
    data: bytes
    readable_value: bool
    content_type: str

    def __init__(self, *, data: bytes, readable: bool = True,
                 content_type: str = 'application/pdf'):
        self.data = data
        self.status = 200 if self.data is not None else 404
        self.readable_value = readable
        self.content_type = content_type

    def read(self):
        self.status = 200 if self.data is not None else 404
        return self.data

    def readable(self):
        return self.readable_value

    def close(self):
        pass

    def getheader(self, name: str = ''):
        if (name == 'Content-Type'):
            return self.content_type
        return None


class FakePngResponse:
    status: int
    data: bytes
    readable_value: bool
    content_type: str

    def __init__(self, *, data: bytes, readable: bool = True,
                 content_type: str = 'image/png'):
        self.data = data
        self.status = 200 if self.data is not None else 404
        self.readable_value = readable
        self.content_type = content_type

    def read(self):
        self.status = 200 if self.data is not None else 404
        return self.data

    def readable(self):
        return self.readable_value

    def close(self):
        pass

    def getheader(self, name: str = ''):
        if (name == 'Content-Type'):
            return self.content_type
        return None
