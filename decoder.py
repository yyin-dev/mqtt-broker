class Decoder:
    def __init__(self, data):
        self.data = data
        self.curr = 0

    def byte(self) -> int:
        b = self.data[self.curr]
        self.curr += 1
        return b

    def bytes(self, n) -> bytes:
        data = self.data[self.curr : self.curr + n]
        self.curr += n
        return data

    def int(self) -> int:
        data = self.data[self.curr : self.curr + 2]
        value = int.from_bytes(data, byteorder="big")
        self.curr += 2
        return value

    def varint(self) -> int:
        res = 0
        shift = 0

        while True:
            b = self.data[self.curr]

            res = res | ((b & 0x7F) << shift)
            self.curr += 1

            if b & 0x80 == 0:
                break

            shift += 7

        return res

    def string(self) -> str:
        length = self.int()

        if length == 0:
            return ""

        data = self.data[self.curr : self.curr + length]
        self.curr += length
        return data.decode("utf-8")

    def num_bytes_consumed(self) -> int:
        return self.curr

    def consumed_all(self) -> bool:
        return self.curr == len(self.data)

    def bytes_consumed(self) -> bytes:
        """
        Returns bytes consumed so far.
        """
        return self.data[: self.curr]
