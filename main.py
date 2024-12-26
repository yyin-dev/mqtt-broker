from typing import Dict, Set
from socket import socket
from protocol import (
    MqttConnack,
    MqttConnect,
    MqttPublish,
    MqttPuback,
    MqttPubrec,
    MqttSubscribe,
    MqttSuback,
    MqttPingreq,
    MqttPingresp,
    MqttDisconnect,
    QosLevel,
    deserialize_mqtt_message,
)
import socketserver
import uuid


class Server(socketserver.ThreadingTCPServer):
    # How to pass argument to server constructor?
    # https://stackoverflow.com/a/14133194/9057530
    def __init__(self, server_address, RequestHandlerClass):
        socketserver.ThreadingTCPServer.__init__(
            self, server_address, RequestHandlerClass
        )

        self.subscriptions: Dict[str, Set[bytes]] = {}  # maps topic name to client ids
        self.clients: Dict[bytes, socket] = {}  # maps client id to socket

    def server_activate(self):
        print("Server is being activated!")
        super().server_activate()

    def process_request(self, request, client_address):
        print(f"Process request {request} from {client_address}")
        super().process_request(request, client_address)


class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        # How to share variables among handlers?
        # self refers to the handler object and is distinct for each request
        # self.server refers to the server object and is shared among handlers
        # https://stackoverflow.com/a/6875827/9057530
        print(f"== Client connected ==")

        # Variables used throughout the lifetime of this handler
        self.client_id = None

        while True:
            # self.connection is a socket.socket
            # https://docs.python.org/3/library/socket.html#socket-objects
            # socket.recv() returns a bytes object
            data = self.connection.recv(1024)
            # print(data)

            if len(data) == 0:
                break

            while len(data) > 0:
                request, bytes_consumed = deserialize_mqtt_message(data)
                print(f"Received: {request}")

                match request:
                    case MqttConnect(
                        protocol_name,
                        protocol_level,
                        connect_flags,
                        keep_alive,
                        client_id,
                    ):
                        # Todo: validation
                        print(f"Client(id='{client_id}') connected")

                        if client_id == "":
                            # The doc says we have two choices:
                            # 1. Reject and respond return_code = 0x02
                            # 2. Assign a unique id to the client
                            #
                            # `mqtt test` passes in an empty client id and
                            # gives up if rejected, so we do #2.
                            client_id = str(uuid.uuid4())
                            print(
                                f"Received empty client id. Assign an unique id: {client_id}"
                            )

                        self.client_id = client_id
                        self.server.clients[client_id] = self.connection

                        connack = MqttConnack(return_code=0)
                        self.connection.sendall(connack.serialize())
                        print(f"CONNACK sent")
                    case MqttPublish(
                        dup_flag, qos_level, retain, topic, packet_id, message
                    ):
                        match qos_level:
                            case QosLevel.AT_MOST_ONCE:
                                pass
                            case QosLevel.AT_LEAST_ONCE:
                                print(f"Unsupported QoS level: {qos_level}!!!")

                                puback = MqttPuback(packet_id)
                                self.connection.sendall(puback.serialize())
                                print(f"PUBACK sent")
                            case QosLevel.EXACTLY_ONCE:
                                print(f"Unsupported QoS level: {qos_level}!!!")

                                puback = MqttPubrec(packet_id)
                                self.connection.sendall(puback.serialize())
                                print(f"PUBACK sent")

                        if topic not in self.server.subscriptions:
                            self.server.subscriptions[topic] = set()

                        for client_id in self.server.subscriptions[topic]:
                            client_conn = self.server.clients[client_id]
                            client_conn.sendall(bytes_consumed)
                    case MqttSubscribe(packet_id, topics):
                        # Check unsupported qos-level
                        return_codes = []
                        for topic, qos_level in topics:
                            if qos_level is not QosLevel.AT_MOST_ONCE:
                                raise NotImplementedError

                            # In MQTT, clients can subscribe to a topic before
                            # any message is published to that topic.
                            if topic not in self.server.subscriptions:
                                self.server.subscriptions[topic] = set()

                            self.server.subscriptions[topic].add(self.client_id)

                            print(f"Subscribe to {topic}, {qos_level}")
                            return_codes.append(0x00)

                        print(f"Subscriptions: {self.server.subscriptions}")

                        # Respond SUBACK
                        suback = MqttSuback(packet_id, return_codes)
                        self.connection.sendall(suback.serialize())
                        print(f"SUBACK sent")
                    case MqttPingreq():
                        pingresp = MqttPingresp()
                        self.connection.sendall(pingresp.serialize())
                        print("PINGRESP sent")
                    case MqttDisconnect():
                        # Remove client
                        del self.server.clients[self.client_id]

                        for topic, subscribers in self.server.subscriptions.items():
                            subscribers.discard(self.client_id)

                        break
                    case unknown:
                        print(f"Unknown: {unknown}")
                        raise NotImplementedError

                data = data[len(bytes_consumed) :]

        print("Client disconnected!")


def main():
    socketserver.ThreadingTCPServer.allow_reuse_address = 1

    server = Server(("localhost", 1883), Handler)
    server.serve_forever()


if __name__ == "__main__":
    main()
