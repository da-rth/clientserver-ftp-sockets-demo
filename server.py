import os
import sys
import socket
import select
import utils
from contextlib import suppress


class FTPServer:

    MSG_BUFFER = 8192
    MAX_CONNECTIONS = 10

    def __init__(self):
        """
        :param port:
        """
        self.dir = os.getcwd()
        self.port = utils.check_args_port()
        self.public_ip = utils.get_ip_address()
        self.srv_socket = None
        self.server_is_running = False
        self.conns = []

    # Commands
    def list_files(self):
        files_dirs = os.walk(self.dir)
        file_list = [" ".join([utils.get_filesize(x[0]), x[0].replace(self.dir, '')]) for x in files_dirs]
        return utils.files_as_tree(file_list)

    def put_file(self, args):
        return "putting file onto server"+str(args)

    def get_file(self, args):
        return "getting file for download"+str(args)

    # Main Program
    def loop_socket_check(self):

        while self.server_is_running:

            with suppress(socket.error):
                # Using select.select to obtain the read ready sockets in the connections list (self.conns)
                read_connections = select.select(self.conns, [], [], 30)[0]

            for connection in read_connections:

                if connection == self.srv_socket:
                    try:
                        cli_sock, (ip, port) = self.srv_socket.accept()
                    except socket.error:
                        break
                    self.conns.append(cli_sock)
                    print("[CON] Client [%s:%s] has connected\n" % (ip, port))

                else:
                    try:
                        args = connection.recv(1024).decode('utf').split(" ")

                        if args:
                            ip, port = connection.getpeername()
                            valid_cmd = True
                            command = args[0]
                            args = args[1:]

                            if command == "list":
                                result = self.list_files()

                            elif command == "put":
                                result = self.put_file(args)

                            elif command == "get":
                                result = self.put_file(args)
                            else:
                                result = "Invalid flags."
                                valid_cmd = False

                            if valid_cmd:
                                utils.error_print("[CMD] Client [%s:%s] has executed command: %s\n" % (ip, port, command))
                            else:
                                print("[ERR] Client [%s:%s] tried to execute invalid command: %s\n" % (ip, port, command))

                            connection.sendall(result.encode())

                    except socket.error:
                        ip, port = connection.getpeername()
                        connection.close()
                        self.conns.remove(connection)
                        print("[DIS] Client [%s:%s] has disconnected\n" % (ip, port))

    def start(self):

        #utils.clear_terminal()

        print(
            "\nLaunching server at:"
            "\n- IP: %s"
            "\n- Port: %s"
            "\n- Directory: %s"
            "\n" % (self.public_ip, self.port, self.dir)
        )

        # Create socket and add to connections list
        self.srv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.srv_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.srv_socket.bind(('', self.port))
        self.srv_socket.listen(self.MAX_CONNECTIONS)
        self.conns.append(self.srv_socket)
        self.server_is_running = True

        print("Waiting for client(s) to connect...\n")

        # Loop checking server for new connections and data
        self.loop_socket_check()

        # If self.server_is_running is false, close server.
        self.srv_socket.close()


if __name__ == '__main__':
    server = FTPServer()
    server.start()
