import os
import socket
import select
import utils
import threading


class FTPServer(threading.Thread):

    MSG_BUFFER = 8192
    MAX_CONNECTIONS = 10

    def __init__(self):
        """
        :param port:
        """
        threading.Thread.__init__(self)
        self.dir = os.getcwd()
        self.port = utils.check_args_port()
        self.public_ip = utils.get_ip_address()
        self.srv_socket = None
        self.server_is_running = False
        self.conns = []
        self.current_conn = {}
        self.commands = {
            "PUT": self.save_file,
            "GET": self.send_file,
            "LIST": self.list_files,
            "DISCONNECT": self.disconnect
        }

    # Commands
    def list_files(self):
        ip, port = self.current_conn['address']

        print("[CMD] Client [%s:%s] has executed command: LIST." % (ip, port))

        files_dirs = os.listdir(os.getcwd())
        file_list = "\n".join([" - [DIR] "+file if os.path.isdir(file) else " - [FIL] "+file for file in files_dirs])
        self.current_conn['socket'].sendall(file_list.encode('utf'))

        print("[OK!] Successfully sent file list of current directory to Client [%s:%s]." % (ip, port))

    def send_file(self):
        ip, port = self.current_conn['address']
        filename = self.current_conn['command'][1]

        print("[CMD] Client [%s:%s] has executed command: GET %s" % (ip, port, filename))

        if filename not in os.listdir(os.getcwd()):
            self.current_conn['socket'].sendall("FileNotFound".encode('utf'))
            print("[ERR] File '%s' could not be found in server directory." % filename)
        else:
            print("[OK!] File '%s' found in server directory. Sending client total file size of file." % filename)

            # send client the filesize of file being sent.
            filesize = str(os.path.getsize(os.getcwd()+'/'+filename))
            self.current_conn['socket'].sendall(filesize.encode())

            upload = open(os.getcwd()+'/'+filename, 'rb')
            data = upload.read(4096)
            while data:
                self.current_conn['socket'].sendall(data)
                data = upload.read(4096)

            print("[OK!] Client [%s:%s] has downloaded file '%s' from server." % (ip, port, filename))

    def save_file(self):
        ip, port = self.current_conn['address']
        filename = self.current_conn['command'][1]

        print("[CMD] Client [%s:%s] has executed command: PUT %s." % (ip, port, filename))

        response = self.current_conn['socket'].recv(1024).decode()

        if response == "FileNotFound":
            print("[ERR] Client response: \"%s\": '%s' does not exist in current client directory." % (response, filename))
            return

        file_size = int(response)
        print("[OK!] Recieved file size for '%s' from server: %s." % (filename, file_size))

        with open(filename, 'wb') as download_file:
            data = self.current_conn['socket'].recv(4096)
            bytes_collected = 0

            while data and (bytes_collected < file_size):
                bytes_collected += len(data)
                download_file.write(data)
                if len(data) < 4096:
                    break
                data = self.current_conn['socket'].recv(4096)

        print("[OK!] Client [%s:%s] has successfully upload file '%s' to the server." % (ip, port, filename))
        print("[OK!] File has been downloaded to the current working directory: %s/%s" % (os.getcwd(), filename))

    def disconnect(self, conn):
        print("[DIS] Client [%s:%s] has disconnected." % conn.getpeername())
        conn.close()
        self.conns.remove(conn)
    # Main Program
    def loop_socket_check(self):

        while self.server_is_running:

            try:
                # Using select.select to obtain the read ready sockets in the connections list (self.conns)
                read_connections = select.select(self.conns, [], [], 30)[0]
            except socket.error:
                continue

            for connection in read_connections:

                if connection == self.srv_socket:
                    try:
                        cli_sock, (ip, port) = self.srv_socket.accept()
                    except socket.error:
                        break
                    self.conns.append(cli_sock)
                    print("[CON] Client [%s:%s] has connected." % (ip, port))

                else:
                    try:

                        self.current_conn = {
                            'socket': connection,
                            'command': connection.recv(1024).decode().split(" "),
                            'address': connection.getpeername()
                        }

                        command_type = self.current_conn['command'][0] if self.current_conn['command'] else None

                        if command_type == "DISCONNECT":
                            self.disconnect(connection)
                        elif command_type:
                            self.commands[command_type]()

                    except socket.error:
                        self.disconnect(connection)

    def start(self):

        utils.clear_terminal()

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
