from enum import Enum
from decoder import Decoder

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


class MqttConnect:
    # Flags should be all zeros.
    # Remaing length includes variable header and payload.
    #
    # Variable header: 10 bytes. Four fields: protocol name (6 bytes),
    # protocol level (1 byte), connect flags (one byte), keep alive (2 bytes).

    def __init__(
        self, protocol_name, protocol_level, connect_flags, keep_alive, client_id
    ):
        self.protocol_name = protocol_name
        self.protocol_level = protocol_level
        self.connect_flags = connect_flags
        self.keep_alive = keep_alive
        self.client_id = client_id

    def __repr__(self):
        return f"{self.__class__.__name__}{str(self.__dict__)}"


def parse_mqtt_connect(data):
    """
    Returns (message, bytes_used)
    """
    decoder = Decoder(data)

    # Fixed header: MQTT type; Flags; Remaining length
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


def parse_mqtt_message(data):
    """
    Returns (message, bytes_used)
    """
    decoder = Decoder(data)

    b = decoder.byte()
    mqtt_type = b >> 4

    parse_funcs = [parse_mqtt_connect]
    parse_func = parse_funcs[mqtt_type - 1]
    msg, num_bytes_consumed = parse_func(data)
    print(msg)
    return msg, num_bytes_consumed
