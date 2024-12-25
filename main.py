import socketserver


class Server(socketserver.ThreadingTCPServer):
    def server_activate(self):
        print("Server is being activated!")
        super().server_activate()

    def finish_request(self, request, client_address):
        print(f"Handling request from {client_address}")
        super().finish_request(request, client_address)


class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        # self.server refers to the server object
        print("Handle!")


def main():
    socketserver.ThreadingTCPServer.allow_reuse_address = 1

    server = Server(("localhost", 1883), Handler)
    server.serve_forever()


if __name__ == "__main__":
    main()
