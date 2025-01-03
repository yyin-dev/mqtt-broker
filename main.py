from socket import socket
import threading
import time
from typing import Dict, Set, Tuple, List
from protocol import (
    MqttConnack,
    MqttConnect,
    MqttPublish,
    MqttPuback,
    MqttPubrec,
    MqttPubrel,
    MqttPubcomp,
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

        # maps topic name to client ids
        self.subscriptions: Dict[str, Set[str]] = {}

        # maps client id to socket
        self.clients: Dict[str, socket] = {}

        # maps packet-id to subscribers
        self.at_least_once_messages: Dict[
            bytes, Tuple[Tuple[MqttPublish, bytes], Set[str]]
        ] = {}

        # maps packet-id to message
        self.releasable_exactly_once_messages: Dict[
            bytes, Tuple[MqttPublish, bytes]
        ] = {}

        # maps packet-id to a list of (mesage, bytes, subscribers)
        self.exactly_once_messages: Dict[
            bytes, List[Tuple[Tuple[MqttPublish, bytes], Set[str]]]
        ] = {}

        # for debugging
        self.thread_cnt = 0

        threading.Thread(target=self.resend_messages).start()

    def resend_messages(self):
        while True:
            dels = []
            for packet_id, (_, subscribers) in self.at_least_once_messages.items():
                subscribers = subscribers.intersection(self.clients.keys())
                if len(subscribers) == 0:
                    dels.append(packet_id)

            for packet_id in dels:
                del self.at_least_once_messages[packet_id]

            dels = []
            for packet_id, vs in self.exactly_once_messages.items():
                noMoreSubscribers = True
                for (msg, b), subscribers in vs:
                    subscribers = subscribers.intersection(self.clients.keys())
                    if len(subscribers) > 0:
                        noMoreSubscribers = False

                if noMoreSubscribers:
                    dels.append(packet_id)

            for packet_id in dels:
                del self.exactly_once_messages[packet_id]

            # At least once messages
            if len(self.at_least_once_messages) > 0:
                print("Retransmitting at-least-once messages!")

                # Remove disconnected subscriber if any
                for packet_id, (
                    (msg, b),
                    subscribers,
                ) in self.at_least_once_messages.items():
                    print(f"Retransmitting {msg} to {subscribers}")
                    for subscriber in subscribers:
                        socket = self.clients[subscriber]
                        socket.sendall(b)

            # Exactly once messages
            if len(self.exactly_once_messages) > 0:
                print("Retransmitting exactly-once messages!")

                # Remove disconnected subscriber if any
                for packet_id, msgs in self.exactly_once_messages.items():
                    for (msg, b), subscribers in msgs:
                        print(f"Retransmitting {msg} to {subscribers}")
                        for subscriber in subscribers:
                            socket = self.clients[subscriber]
                            socket.sendall(b)

            time.sleep(2)

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
        self.thread_id = self.server.thread_cnt
        self.server.thread_cnt += 1

        while True:
            # self.connection is a socket.socket
            # https://docs.python.org/3/library/socket.html#socket-objects
            # socket.recv() returns a bytes object
            data = self.connection.recv(1024)
            # print(data)

            if not data:
                print(f"[{self.thread_id}] == Client {self.client_id} disconnected ==")
                break

            while len(data) > 0:
                print(data)

                request, bytes_consumed = deserialize_mqtt_message(data)
                print(
                    f"[{self.thread_id}] Received: {request} from client: {self.client_id}"
                )

                match request:
                    case MqttConnect(
                        protocol_name,
                        protocol_level,
                        connect_flags,
                        keep_alive,
                        client_id,
                    ):
                        # Todo: validation
                        print(f"[{self.thread_id}] Client(id='{client_id}') connected")

                        if client_id == "":
                            # The doc says we have two choices:
                            # 1. Reject and respond return_code = 0x02
                            # 2. Assign a unique id to the client
                            #
                            # `mqtt test` passes in an empty client id and
                            # gives up if rejected, so we do #2.
                            client_id = str(uuid.uuid4())
                            print(
                                f"[{self.thread_id}] Received empty client id. Assign an unique id: {client_id}"
                            )

                        self.client_id = client_id
                        self.server.clients[client_id] = self.connection

                        connack = MqttConnack(return_code=0)
                        self.connection.sendall(connack.serialize())
                        print(f"[{self.thread_id}] CONNACK sent")
                    case MqttPublish(
                        dup_flag, qos_level, retain, topic, packet_id, message
                    ) as mqtt_publish:
                        if topic not in self.server.subscriptions:
                            self.server.subscriptions[topic] = set()

                        match qos_level:
                            case QosLevel.AT_MOST_ONCE:
                                for client_id in self.server.subscriptions[topic]:
                                    client_conn = self.server.clients[client_id]
                                    client_conn.sendall(bytes_consumed)
                            case QosLevel.AT_LEAST_ONCE:
                                puback = MqttPuback(packet_id)
                                self.connection.sendall(puback.serialize())
                                print(f"[{self.thread_id}] PUBACK sent")

                                for client_id in self.server.subscriptions[topic]:
                                    client_conn = self.server.clients[client_id]
                                    client_conn.sendall(bytes_consumed)

                                # Mark message as to be delivered at least once
                                self.server.at_least_once_messages[packet_id] = (
                                    (mqtt_publish, bytes_consumed),
                                    self.server.subscriptions[
                                        topic
                                    ].copy(),  # copy() is important here! Python pass by object reference
                                )
                            case QosLevel.EXACTLY_ONCE:
                                puback = MqttPubrec(packet_id)
                                self.connection.sendall(puback.serialize())
                                print(f"[{self.thread_id}] PUBACK sent")

                                # Mark message as pending release
                                self.server.releasable_exactly_once_messages[
                                    packet_id
                                ] = (mqtt_publish, bytes_consumed)

                    case MqttPuback(packet_id):
                        print(
                            f"[{self.thread_id}] Received PUBACK for {packet_id} from {client_id}"
                        )

                        if packet_id not in self.server.at_least_once_messages:
                            # This is possible when we receive PUBACK for the
                            # same packet_id from a client more than once.
                            pass
                        else:
                            _, subscribers = self.server.at_least_once_messages[
                                packet_id
                            ]
                            subscribers.discard(self.client_id)

                            if len(subscribers) == 0:
                                print(
                                    f"[{self.thread_id}] Recevied PUBACK from all subscribers of {packet_id}!"
                                )
                                del self.server.at_least_once_messages[packet_id]

                    case MqttPubrec(packet_id):
                        print(
                            f"[{self.thread_id}] Received PUBREC for {packet_id} from subscriber {self.client_id}"
                        )

                        # Send PUBREL
                        pubrel = MqttPubrel(packet_id)
                        self.connection.sendall(pubrel.serialize())
                        print(f"[{self.thread_id}] PUBREL sent")
                    case MqttPubrel(packet_id):
                        print(
                            f"[{self.thread_id}] Received PUBREL for {packet_id} from publisher {self.client_id}"
                        )

                        if packet_id in self.server.releasable_exactly_once_messages:
                            # send PUBCOMP
                            pubcomp = MqttPubcomp(packet_id)
                            self.connection.sendall(pubcomp.serialize())
                            print(f"[{self.thread_id}] PUBCOMP sent")

                            mqtt_publish, mqtt_publish_bytes = (
                                self.server.releasable_exactly_once_messages[packet_id]
                            )

                            if packet_id not in self.server.exactly_once_messages:
                                self.server.exactly_once_messages[packet_id] = []

                            current_subscribers = self.server.subscriptions[
                                mqtt_publish.topic
                            ].copy()

                            for subscriber in current_subscribers:
                                self.server.clients[subscriber].sendall(
                                    mqtt_publish_bytes
                                )

                            self.server.exactly_once_messages[packet_id].append(
                                (
                                    (mqtt_publish, mqtt_publish_bytes),
                                    current_subscribers,
                                )
                            )
                            del self.server.releasable_exactly_once_messages[packet_id]

                            print(
                                f"[{self.thread_id}] Exactly once messages to be sent: {self.server.exactly_once_messages}"
                            )

                    case MqttPubcomp(packet_id):
                        print(
                            f"[{self.thread_id}] Received PUBCOMP for {packet_id} from subscriber {self.client_id}"
                        )

                        if packet_id not in self.server.exactly_once_messages:
                            # This is possible when we receive PUBCOMP for the
                            # same packet_id from a client more than once.
                            pass
                        else:
                            messages = self.server.exactly_once_messages[packet_id]
                            _, subscribers = messages[0]
                            subscribers.discard(self.client_id)

                            if len(subscribers) == 0:
                                print(
                                    f"[{self.thread_id}] Recevied PUBCOMP from all subscribers of {packet_id}!"
                                )
                                del messages[0]

                                if len(messages) == 0:
                                    del self.server.exactly_once_messages[packet_id]

                    case MqttSubscribe(packet_id, topics):
                        # Check unsupported qos-level
                        return_codes = []
                        for topic, qos_level in topics:
                            # In MQTT, clients can subscribe to a topic before
                            # any message is published to that topic.
                            if topic not in self.server.subscriptions:
                                self.server.subscriptions[topic] = set()

                            self.server.subscriptions[topic].add(self.client_id)

                            print(
                                f"[{self.thread_id}] Subscribe to {topic}, {qos_level}"
                            )
                            return_codes.append(0x00)

                        print(
                            f"[{self.thread_id}] Subscriptions: {self.server.subscriptions}"
                        )

                        # Respond SUBACK
                        suback = MqttSuback(packet_id, return_codes)
                        self.connection.sendall(suback.serialize())
                        print(f"[{self.thread_id}] SUBACK sent")
                    case MqttPingreq():
                        pingresp = MqttPingresp()
                        self.connection.sendall(pingresp.serialize())
                        print(f"[{self.thread_id}] PINGRESP sent")
                    case MqttDisconnect():
                        # Remove client
                        del self.server.clients[self.client_id]

                        for topic, subscribers in self.server.subscriptions.items():
                            subscribers.discard(self.client_id)

                        break
                    case unknown:
                        print(f"[{self.thread_id}] Unknown: {unknown}")
                        raise NotImplementedError

                data = data[len(bytes_consumed) :]

        if self.client_id in self.server.clients:
            del self.server.clients[self.client_id]

        for topic, subscribers in self.server.subscriptions.items():
            subscribers.discard(self.client_id)


def main():
    socketserver.ThreadingTCPServer.allow_reuse_address = 1

    server = Server(("localhost", 1883), Handler)
    server.serve_forever()


if __name__ == "__main__":
    main()
