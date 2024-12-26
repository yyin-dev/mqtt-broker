from dataclasses import dataclass
from decoder import Decoder
from encoder import Encoder
from enum import Enum

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
        decoder.num_bytes_consumed(),
    )


@dataclass
class MqttConnack:
    return_code: int

    def serialize(self) -> bytes:
        encoder = Encoder()

        # Fixed header
        # byte 1: \0x20. Packet type | flags
        # byte 2: \0x02. Remaining length
        encoder.append_byte(0x20)
        encoder.append_byte(0x02)

        # variable header:
        # byte 1: \x00. connect ack flags and session present flag
        # byte 2: connect return code
        encoder.append_byte(0x00)
        encoder.append_byte(self.return_code)

        return encoder.bytes()


@dataclass
class MqttPublish:
    message: str


# Albegraic type: https://stackoverflow.com/q/16258553/9057530
MqttRequest = MqttConnect | MqttPublish


def deserialize_mqtt_message(data) -> tuple[MqttRequest, int]:
    """
    Returns (message, bytes_used)
    """
    decoder = Decoder(data)

    b = decoder.byte()
    mqtt_type = b >> 4
    print(MessageType(mqtt_type))

    deserialize_funcs = [deserialize_mqtt_connect]
    deserialize_func = deserialize_funcs[mqtt_type - 1]
    msg, num_bytes_consumed = deserialize_func(data)
    return msg, num_bytes_consumed
