import sys
import os
import socket
import select
from contextlib import suppress


def files_as_tree(files_list, subtree_level=0, res=None):

    if len(files_list) == 0:
        return "Empty directory"

    indentation = '\t' * (subtree_level-1)
    subdirectory_text = '|-- ' if subtree_level > 0 else ''
    directory_list = "".join([indentation, subdirectory_text, files_list[0], '\n'])

    for file in files_list[1:]:
        if type(file) is list:
            files_as_tree(file, subtree_level+1, directory_list)
        else:
            line = "".join([indentation, subdirectory_text, file, '\n'])
            directory_list = "".join([directory_list, line])

    return directory_list


def get_filesize(filepath):

    size = float(os.path.getsize(filepath))
    sizes = [' b', 'kb', 'mb', 'gb']
    i = 0
    while size > 1024 and i < 5:
        size = size / 1024.00
        i += 1

    return "(%0.2f%s)" % (size, sizes[i])


class FTPServer:

    # Constants
    MSG_BUFFER = 4096
    MAX_CONNECTIONS = 10

    def __init__(self):
        """
        :param port:
        """
        self.dir = os.getcwd()
        self.port = self.check_args_port()
        self.public_ip = self.get_ip_address()
        self.srv_socket = None
        self.server_is_running = False
        self.conns = []

        self.commands = {
            "put": self.put_file,
            "get": self.get_file,
            "list": self.list_files
        }

    # Commands
    def list_files(self, flags):
        files_dirs = os.walk(self.dir)
        file_list = [" ".join([get_filesize(x[0]), x[0].strip(self.dir)]) for x in files_dirs]
        return files_as_tree(file_list)

    def put_file(self, flags):
        return "putting file onto server"

    def get_file(self, flags):
        return "getting file for download"

    # Utilities
    @staticmethod
    def clear_terminal():
        os.system('clear' if os.name != 'nt' else 'cls')

    @staticmethod
    def check_args_port():
        error_msg = "Error, port number expected as argument (e.g. python server.py 8080)"

        if len(sys.argv) < 2:
            raise SystemExit(error_msg)

        port = sys.argv[1]
        # Throw sysexit if port is less than 1 or is greater than 99999 or is not a digit.
        if (not (1 <= len(port) <= 5)) or (not port.isdigit()):
            raise SystemExit(error_msg)
        else:
            return int(port)

    @staticmethod
    def get_ip_address():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # Try connect to google public DNS and get name (IP) of socket.
            s.connect(("8.8.8.8", 80))
            ip_address = s.getsockname()[0]
        except socket.gaierror:
            # If we can't reach google's DNS, show localhost as IP
            ip_address = "127.0.0.1"
        finally:
            s.close()
        return ip_address

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
                        command = connection.recv(1024).decode('utf')

                        if command:
                            ip, port = connection.getpeername()
                            print("[CMD] Client [%s:%s] has executed command: %s\n" % (ip, port, command))

                            command = command.split(" ")

                            if command[0] in self.commands:
                                flags = command[1:] if len(command) > 1 else []
                                response = self.commands[command[0]](flags)
                            else:
                                response = "Invalid command. Please try [put], [get], or [list]"
                            cli_sock.sendall(response.encode())

                    except socket.error:
                        ip, port = connection.getpeername()
                        connection.close()
                        self.conns.remove(connection)
                        print("[DIS] Client [%s:%s] has disconnected\n" % (ip, port))

    def start(self):

        self.clear_terminal()

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
