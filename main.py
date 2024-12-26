from protocol import (
    MqttConnack,
    MqttConnect,
    MqttPublish,
    MqttSubscribe,
    MqttSuback,
    MqttPingreq,
    MqttPingresp,
    MqttDisconnect,
    QosLevel,
    deserialize_mqtt_message,
)
import socketserver


class Server(socketserver.ThreadingTCPServer):
    # How to pass argument to server constructor?
    # https://stackoverflow.com/a/14133194/9057530
    def __init__(self, server_address, RequestHandlerClass):
        socketserver.ThreadingTCPServer.__init__(
            self, server_address, RequestHandlerClass
        )
        self.request_count = 0

    def server_activate(self):
        print("Server is being activated!")
        super().server_activate()

    def process_request(self, request, client_address):
        print(f"Process request {request} from {client_address}")
        self.request_count += 1
        super().process_request(request, client_address)

    def finish_request(self, request, client_address):
        print(f"Handling request from {client_address}")
        super().finish_request(request, client_address)


class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        # How to share variables among handlers?
        # self refers to the handler object and is distinct for each request
        # self.server refers to the server object and is shared among handlers
        # https://stackoverflow.com/a/6875827/9057530
        print(f"== Request #{self.server.request_count} ==")

        while True:
            # self.connection is a socket.socket
            # https://docs.python.org/3/library/socket.html#socket-objects
            # socket.recv() returns a bytes object
            data = self.connection.recv(1024)

            if len(data) == 0:
                break

            while len(data) > 0:
                request, num_bytes_consumed = deserialize_mqtt_message(data)
                print(request)

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

                        connack = MqttConnack(return_code=0)
                        self.connection.sendall(connack.serialize())
                        print(f"CONNACK sent")
                    case MqttPublish(
                        dup_flag, qos_level, retain, topic_name, packet_id, message
                    ):
                        match qos_level:
                            case QosLevel.AT_MOST_ONCE:
                                pass
                            case QosLevel.AT_LEAST_ONCE:
                                raise NotImplementedError
                            case QosLevel.EXACTLY_ONCE:
                                raise NotImplementedError
                    case MqttSubscribe(packet_id, topics):
                        # Check unsupported qos-level
                        return_codes = []
                        for topic, qos_level in topics:
                            if qos_level is not QosLevel.AT_MOST_ONCE:
                                raise NotImplementedError

                            print(f"Subscribe to {topic}, {qos_level}")
                            return_codes.append(0x00)

                        # Respond SUBACK
                        suback = MqttSuback(packet_id, return_codes)
                        self.connection.sendall(suback.serialize())
                        print(f"SUBACK sent")
                    case MqttPingreq():
                        pingresp = MqttPingresp()
                        self.connection.sendall(pingresp.serialize())
                        print("PINGRESP sent")
                    case MqttDisconnect():
                        break
                    case unknown:
                        print(f"Unknown: {unknown}")
                        raise NotImplementedError

                data = data[num_bytes_consumed:]

        print("Client disconnected!")


def main():
    socketserver.ThreadingTCPServer.allow_reuse_address = 1

    server = Server(("localhost", 1883), Handler)
    server.serve_forever()


if __name__ == "__main__":
    main()
