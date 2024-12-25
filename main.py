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
        print(f"Request #{self.server.request_count}")


def main():
    socketserver.ThreadingTCPServer.allow_reuse_address = 1

    server = Server(("localhost", 1883), Handler)
    server.serve_forever()


if __name__ == "__main__":
    main()
