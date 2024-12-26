class Encoder:
    def __init__(self):
        self.data = bytes()

    def append_byte(self, b):
        self.data += int.to_bytes(b, length=1, byteorder="big", signed=False)

    def append_int(self, v):
        self.data += int.to_bytes(v, length=2, byteorder="big", signed=False)

    def bytes(self) -> bytes:
        return self.data
