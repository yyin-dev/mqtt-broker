from dataclasses import dataclass
from decoder import Decoder
from encoder import Encoder
from enum import Enum
from typing import List, Tuple

"""
Message = | Fixed header | Variable header (optional) | Payload (optional)

Fixed header
| Bit    | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|--------|---------------|---------------|
| Byte 1 | MQTT type     |  Flags        |
|--------|-------------------------------|
| Byte 2 |                               |
|  ...   |      Remaining Length         |

"""


class MessageType(Enum):
    CONNECT = 1
    CONNACK = 2
    PUBLISH = 3
    PUBACK = 4
    PUBREC = 5
    PUBREL = 6
    PUBCOMP = 7
    SUBSCRIBE = 8
    SUBACK = 9
    UNSUBSCRIBE = 10
    UNSUBACK = 11
    PINGREQ = 12
    PINGRESP = 13
    DISCONNECT = 14


class QosLevel(Enum):
    AT_MOST_ONCE = 0
    AT_LEAST_ONCE = 1
    EXACTLY_ONCE = 2


@dataclass
class MqttConnect:
    protocol_name: str
    protocol_level: int
    connect_flags: int
    keep_alive: int
    client_id: str

    def __repr__(self):
        return f"{self.__class__.__name__}{str(self.__dict__)}"


def deserialize_mqtt_connect(data):
    """
    Returns (message, bytes_used)
    """
    decoder = Decoder(data)

    # Fixed header: MQTT type; Flags; Remaining length
    # Flags shoudl all be zero
    # Remaining length includes variable header and payload
    b = decoder.byte()
    mqtt_type = b >> 4
    assert MessageType(mqtt_type) == MessageType.CONNECT
    remaining_length = decoder.varint()
    num_bytes_consumed = decoder.num_bytes_consumed()

    # Variable header
    protocol_name = decoder.string()
    protocol_level = decoder.byte()
    connect_flags = decoder.byte()
    keep_alive = decoder.int()

    # payload
    client_id = decoder.string()
    assert (decoder.num_bytes_consumed() - num_bytes_consumed) == remaining_length

    return (
        MqttConnect(
            protocol_name, protocol_level, connect_flags, keep_alive, client_id
        ),
        decoder.bytes_consumed(),
    )


@dataclass
class MqttConnack:
    return_code: int

    def serialize(self) -> bytes:
        encoder = Encoder()

        # Fixed header
        # byte 1: \0x20. Packet type | flags
        # byte 2: Remaining length 2
        encoder.append_byte(0x20)
        encoder.append_varint(2)

        # variable header:
        # byte 1: \x00. connect ack flags and session present flag
        # byte 2: connect return code
        encoder.append_byte(0x00)
        encoder.append_byte(self.return_code)

        return encoder.bytes()


@dataclass
class MqttPublish:
    dup_flag: bool
    qos_level: QosLevel
    retain: bool
    topic: str
    packet_id: bytes  # 2 bytes; only present when qos is 1 or 2
    message: str


def deserialize_mqtt_publish(data):
    decoder = Decoder(data)

    # Fixed header
    b = decoder.byte()
    mqtt_type = b >> 4
    assert MessageType(mqtt_type) == MessageType.PUBLISH

    dup_flag = ((b & 0x08)) > 0
    qos_level = QosLevel((b & 0x06) >> 1)
    retain = b & 0x01 > 0
    remaining_len = decoder.varint()
    num_bytes_consumed = decoder.num_bytes_consumed()

    # Variable header
    topic = decoder.string()
    if qos_level == QosLevel.AT_LEAST_ONCE or qos_level == QosLevel.EXACTLY_ONCE:
        packet_id = decoder.bytes(2)
    else:
        packet_id = None

    # payload
    message_length = remaining_len - (decoder.num_bytes_consumed() - num_bytes_consumed)
    message = decoder.bytes(message_length).decode("utf-8")

    return (
        MqttPublish(dup_flag, qos_level, retain, topic, packet_id, message),
        decoder.bytes_consumed(),
    )


@dataclass
class MqttPuback:
    packet_id: bytes  # 2 byte

    def serialize(self):
        encoder = Encoder()

        # fixed header
        # byte1: 0x40
        # byte2: remaining length 2
        encoder.append_byte(0x40)
        encoder.append_varint(2)

        # variable header
        encoder.append_bytes(self.packet_id)

        # no payload

        return encoder.bytes()


def deserialize_mqtt_puback(data):
    decoder = Decoder(data)

    # fixed header
    b = decoder.byte()
    mqtt_byte = b >> 4
    assert MessageType(mqtt_byte) == MessageType.PUBACK

    remaining_len = decoder.varint()
    assert remaining_len == 2

    # variable header
    packet_id = decoder.bytes(2)

    return MqttPuback(packet_id), decoder.bytes_consumed()


@dataclass
class MqttPubrec:
    packet_id: bytes  # 2 byte

    def serialize(self):
        encoder = Encoder()

        # fixed header
        # byte1: 0x50
        # byte2: remaining length 2
        encoder.append_byte(0x50)
        encoder.append_varint(2)

        # variable header
        encoder.append_bytes(self.packet_id)

        # no payload

        return encoder.bytes()


def deserialize_mqtt_pubrec(data):
    decoder = Decoder(data)

    # fixed header
    b = decoder.byte()
    mqtt_byte = b >> 4
    assert MessageType(mqtt_byte) == MessageType.PUBREC

    remaining_len = decoder.varint()
    assert remaining_len == 2

    # variable header
    packet_id = decoder.bytes(2)

    return MqttPubrec(packet_id), decoder.bytes_consumed()


@dataclass
class MqttPubrel:
    packet_id: bytes  # 2 byte

    def serialize(self):
        encoder = Encoder()

        # fixed header
        # byte1: 0x60
        # byte2: remaining length 2
        encoder.append_byte(0x60)
        encoder.append_varint(2)

        # variable header
        encoder.append_bytes(self.packet_id)

        # no payload

        return encoder.bytes()


def deserialize_mqtt_pubrel(data):
    decoder = Decoder(data)

    # fixed header
    b = decoder.byte()
    mqtt_byte = b >> 4
    assert MessageType(mqtt_byte) == MessageType.PUBREL

    remaining_len = decoder.varint()
    assert remaining_len == 2

    # variable header
    packet_id = decoder.bytes(2)

    return MqttPubrel(packet_id), decoder.bytes_consumed()


@dataclass
class MqttPubcomp:
    packet_id: bytes  # 2 byte

    def serialize(self):
        encoder = Encoder()

        # fixed header
        # byte1: 0x70
        # byte2: remaining length 2
        encoder.append_byte(0x70)
        encoder.append_varint(2)

        # variable header
        encoder.append_bytes(self.packet_id)

        # no payload

        return encoder.bytes()


def deserialize_mqtt_pubcomp(data):
    decoder = Decoder(data)

    # fixed header
    b = decoder.byte()
    mqtt_byte = b >> 4
    assert MessageType(mqtt_byte) == MessageType.PUBCOMP

    remaining_len = decoder.varint()
    assert remaining_len == 2

    # variable header
    packet_id = decoder.bytes(2)

    return MqttPubcomp(packet_id), decoder.bytes_consumed()


@dataclass
class MqttSubscribe:
    packet_id: bytes  # 2 bytes
    topics: List[Tuple[str, QosLevel]]


def deserialize_mqtt_subscribe(data):
    decoder = Decoder(data)

    # Fixed header
    b = decoder.byte()
    mqtt_type = b >> 4
    assert MessageType(mqtt_type) == MessageType.SUBSCRIBE
    remaining_len = decoder.varint()
    num_bytes_in_fixed_header = decoder.num_bytes_consumed()

    # Variable header
    packet_id = decoder.bytes(2)

    # Payload
    topics = []
    while not decoder.consumed_all():
        topic = decoder.string()
        qos_level = QosLevel(decoder.byte())
        topics.append((topic, qos_level))

    if decoder.num_bytes_consumed() - num_bytes_in_fixed_header != remaining_len:
        print(f"Consumed: {decoder.num_bytes_consumed()}")
        print(f"Consumed after parsing fixed header: {num_bytes_in_fixed_header}")
        print(
            f"Consumed for variable header and payload: {decoder.num_bytes_consumed() - num_bytes_in_fixed_header}"
        )
        print(f"Expecrted: {remaining_len}")
        raise Exception("Didn't fully consume message")

    return (MqttSubscribe(packet_id, topics), decoder.bytes_consumed())


@dataclass
class MqttSuback:
    packet_id: bytes  # 2 bytes
    return_codes: List[int]  # matching the order of topics in SUBSCRIBE

    def serialize(self):
        # Fixed header
        # byte 1: \0x90
        # byte 2: remaining length, varint
        encoder = Encoder()

        encoder.append_byte(0x90)
        variable_header_len = 2
        payload_len = len(self.return_codes)
        remaining_len = variable_header_len + payload_len
        encoder.append_varint(remaining_len)

        # Variable header
        encoder.append_bytes(self.packet_id)

        # Payload
        for return_code in self.return_codes:
            encoder.append_byte(return_code)

        return encoder.bytes()


@dataclass
class MqttDisconnect:
    pass


def deserialize_mqtt_disconnect(data):
    decoder = Decoder(data)

    # Fixed header
    b = decoder.byte()
    mqtt_type = b >> 4
    assert MessageType(mqtt_type) == MessageType.DISCONNECT
    remaining_len = decoder.varint()
    assert remaining_len == 0

    # no variable header or payload
    return (MqttDisconnect(), decoder.bytes_consumed())


@dataclass
class MqttPingreq:
    pass


def deserialize_mqtt_pingreq(data):
    decoder = Decoder(data)

    # Fixed header
    b = decoder.byte()
    mqtt_type = b >> 4
    assert MessageType(mqtt_type) == MessageType.PINGREQ
    remaining_len = decoder.varint()
    assert remaining_len == 0

    # no variable header or payload
    return (MqttPingreq(), decoder.bytes_consumed())


@dataclass
class MqttPingresp:

    def serialize(self):
        encoder = Encoder()

        # fixed header
        # byte 1: \xD0
        # byte 2: remaining length 0
        encoder.append_byte(0xD0)
        encoder.append_varint(0)

        # no variable header or payload

        return encoder.bytes()


# Albegraic type: https://stackoverflow.com/q/16258553/9057530
MqttRequest = (
    MqttConnect
    | MqttPublish
    | MqttPuback
    | MqttSubscribe
    | MqttDisconnect
    | MqttPingreq
)


def deserialize_mqtt_message(data) -> tuple[MqttRequest, bytes]:
    """
    Returns (message, bytes_consumed)
    """
    decoder = Decoder(data)

    b = decoder.byte()
    mqtt_type = MessageType(b >> 4)
    deserialize_funcs = {
        MessageType.CONNECT: deserialize_mqtt_connect,
        MessageType.PUBLISH: deserialize_mqtt_publish,
        MessageType.PUBACK: deserialize_mqtt_puback,
        MessageType.PUBREC: deserialize_mqtt_pubrec,
        MessageType.PUBREL: deserialize_mqtt_pubrel,
        MessageType.PUBCOMP: deserialize_mqtt_pubcomp,
        MessageType.SUBSCRIBE: deserialize_mqtt_subscribe,
        MessageType.PINGREQ: deserialize_mqtt_pingreq,
        MessageType.DISCONNECT: deserialize_mqtt_disconnect,
    }
    msg, bytes_consumed = deserialize_funcs[mqtt_type](data)
    return msg, bytes_consumed
