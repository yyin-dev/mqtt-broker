class Encoder:
    def __init__(self):
        self.data = bytearray()

    def append_byte(self, b):
        self.data.extend(int.to_bytes(b, length=1, byteorder="big", signed=False))

    def append_bytes(self, v):
        self.data.extend(v)

    def append_int(self, v):
        self.data.extend(int.to_bytes(v, length=2, byteorder="big", signed=False))

    def append_varint(self, v):
        if v < 0:
            raise ValueError("Varint encoding does not support negative values.")

        result = bytearray()
        while v > 0x7F:  # While there are still more significant bits
            result.append((v & 0x7F) | 0x80)  # Add the least 7 bits with MSB set
            v >>= 7  # Shift by 7 bits
        result.append(v & 0x7F)  # Add the remaining 7 bits

        self.data.extend(result)

    def bytes(self) -> bytes:
        return bytes(self.data)
