from __future__ import print_function
import socket
import sys
import os
import re

"""
Client.py
Author: 2086380A
NOSE 2 - Assessment 1

Requires parameters: <domain/ip> <port> <put filename | get filename | list>
FTPClient object requires:
- HOST (IP address or domain)
- PORT (Integer value between 0-99999)
- 
"""
# TODO: Deny over-writing existing files in server directory.
# TODO: Check error handling and reporting
# TODO: Add to server.log?


class FTPClient:

    EXAMPLE_INPUT = "\n - Example input: python client.py <domain/ip> <port> <put filename|get filename|list>"

    def __init__(self, host, port, command):
        self.cli_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = self.check_port(port)
        self.command = self.check_command(command)
        self.filename = None
        self.supported_commands = {
            "put": self.put_file,
            "get": self.get_file,
            "list": self.show_list
        }

    def err_exit(self, message):
        """
        :param message:
        :return:
        """
        raise SystemExit("[ERR] %s" % message)

    @staticmethod
    def get_filesize(size_bytes):
        """
        :param size_bytes:
        :return:
        """
        sizes = ['B', 'KB', 'MB', 'GB']
        i = 0
        while size_bytes > 1024 and i < 5:
            size_bytes = size_bytes / 1024.00
            i += 1
        return "%0.2f%s" % (size_bytes, sizes[i])

    def start(self):
        try:
            self.cli_socket.connect((self.host, self.port))
            print("[CON] Successfully connected to server at: %s:%s" % (self.host, self.port))
        except socket.gaierror:
            self.cli_socket.close()
            self.err_exit("Could not connect to host '%s' at port: %s" % (self.host, self.port))
        else:
            self.supported_commands[self.command[0]]()
            self.cli_socket.sendall("DISCONNECT".encode())
            self.cli_socket.close()
            print("[DIS] Disconnected from server.")

    def upload(self, file):
        """
        :param file:
        :return:
        """
        file_size = str(os.path.getsize(os.getcwd() + '/' + file))
        self.cli_socket.sendall(file_size.encode('utf'))

        with open('%s/%s' % (os.getcwd(), file), 'rb') as upload_file:
            data = upload_file.read(4096)
            bytes_sent = 0
            max_size = self.get_filesize(os.path.getsize(file))
            curr_size = self.get_filesize(bytes_sent)
            while data:
                self.cli_socket.sendall(data)
                bytes_sent += len(data)
                data = upload_file.read(4096)
                curr_size = self.get_filesize(bytes_sent)
                print("[UPL] Uploading '%s' [%s / %s]" % (file, curr_size, max_size), end='\r')
            print("[UPL] Upload Complete '%s' [%s / %s]" % (file, curr_size, max_size))

        print("[OK!] Server has received file '%s' from client" % file)

    def download(self, file, fsize):

        with open(file, 'wb') as download_file:
            data = self.cli_socket.recv(4096)
            bytes_collected = 0
            max_size = self.get_filesize(fsize)
            while data and (bytes_collected < fsize):
                bytes_collected += len(data)
                curr_size = self.get_filesize(bytes_collected)
                download_file.write(data)
                print("[DWN] Downloading '%s' [%s / %s]" % (file, curr_size, max_size), end='\r')
                if len(data) < 4096:
                    print("[DWN] Download Complete '%s' [%s / %s]" % (file, curr_size, max_size))
                    break
                data = self.cli_socket.recv(4096)
        print("[OK!] File saved to: %s/%s" % (os.getcwd(), file))

    # Checkers
    def check_command(self, command):
        cmd_type = command[0]

        if cmd_type not in ["list", "put", "get"]:
            self.err_exit("The parameter %s is not supported by this client. Try: %s" % (cmd_type, self.EXAMPLE_INPUT))

        if (cmd_type == "put" or cmd_type == "get") and len(command) != 2:
            self.err_exit("The \"%s\" command must be followed by the <filename> field. Try: %s" % (cmd_type, self.EXAMPLE_INPUT))

        return command

    def check_host(self, host):

        if host.lower() != "localhost" and (" " in host or not re.match(r"^[a-zA-Z0-9_.-]*$", host)):
            self.err_exit("The domain/IP address provided contains spaces and/or special characters. "
                          "Allowed characters: letters, numbers, periods, dashes and underscores.")
        return host

    def check_port(self, port):

        if not port.isdigit() or not (1 <= len(port) <= 5):
            self.err_exit("The port parameter that has been provided is too short/long or is not a numerical value")
        if int(port) < 0:
            self.err_exit("The port parameter that has been provided is not a positive numerical value")

        return int(port)

    # Command execution
    def put_file(self):

        filename = self.command[1]
        self.cli_socket.sendall(("PUT " + filename).encode())

        print("[CMD] Invoking Server Protocol 'PUT' command with filename: %s" % filename)

        if filename not in os.listdir(os.getcwd()):
            self.cli_socket.sendall("FileNotFound".encode('utf'))
            print("[ERR] File '%s' could not be found in client directory" % filename)
        else:
            print("[OK!] File '%s' found in client directory. Sending total filesize." % filename)
            self.upload(file=filename)

    def get_file(self):

        filename = self.command[1]
        print("[CMD] Invoking Server Protocol 'GET' command with filename: %s" % filename)

        self.cli_socket.sendall(("GET " + filename).encode())
        response = self.cli_socket.recv(1024).decode()

        if response == "FileNotFound":
            self.err_exit("Server response: \"%s\": '%s' does not exist in server directory" % (response, filename))
        else:
            file_size = int(response)
            self.download(file=filename, fsize=int(response))

    def show_list(self):
        # connect to socket, print list of files
        print("[CMD] Invoking Server Protocol 'LIST' command.")
        self.cli_socket.sendall("LIST".encode())
        data = self.cli_socket.recv(4096)
        if data:
            print("[OK!] Server responded with:\n%s" % data.decode())
        else:
            self.err_exit("Server responded without a file list.")


if __name__ == '__main__':

    if len(sys.argv) < 4:
        raise SystemExit("\n[ERR] The domain/IP and port parameters are required:"
                         "\nTry:     python client.py <domain/ip> <port> <parameter>"
                         "\nExample: python client.py  127.0.0.1     8080   list")

    client = FTPClient(host=sys.argv[1], port=sys.argv[2], command=sys.argv[3:])
    client.start()



