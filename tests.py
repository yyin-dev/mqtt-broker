import unittest
from decoder import Decoder
from protocol import deserialize_mqtt_message


class TestDecoder(unittest.TestCase):
    def test_byte(self):
        decoder = Decoder(b"\x00\x01")
        b = decoder.byte()
        self.assertEqual(b, 0)
        b = decoder.byte()
        self.assertEqual(b, 1)

    def test_int(self):
        decoder = Decoder(b"\x00\x01\x00\x10\x00\x08\x01\x00")
        i = decoder.int()
        self.assertEqual(i, 1)
        i = decoder.int()
        self.assertEqual(i, 16)
        i = decoder.int()
        self.assertEqual(i, 8)
        i = decoder.int()
        self.assertEqual(i, 256)

    def test_varint(self):
        self.assertEqual(Decoder(b"\x0a").varint(), 10)
        self.assertEqual(Decoder(b"\x7f").varint(), 127)
        self.assertEqual(Decoder(b"\x81\x01").varint(), 129)

    def test_string(self):
        decoder = Decoder(b"\x00\x08ABCDEFGH")
        s = decoder.string()
        self.assertEqual(s, "ABCDEFGH")


class TestProtocol(unittest.TestCase):
    def test_connect(self):
        data = b"\x10\x18\x00\x04MQTT\x04\x02\x00<\x00\x0cmqttPUbRsGYH"
        res, num_byte_consumed = deserialize_mqtt_message(data)
        self.assertEqual(len(data), num_byte_consumed)


if __name__ == "__main__":
    unittest.main()
