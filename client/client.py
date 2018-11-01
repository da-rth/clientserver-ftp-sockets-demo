from __future__ import print_function
import socket
import sys
import os
import re
import logging
import datetime

"""
client.py - NOSE 2 - Assessment 1

Authors: - Daniel Arthur [2086380A]
         - Kieran Watson [2318086W]

FTPClient object requires:
- HOST (IP address or domain)
- PORT (Integer value between 0-99999)
- COMMANDS (List of Strings: LIST|PUT|GET followed by filename) 

CTRL+C to exit client
"""

EXAMPLE_INPUT = "\n - Example input: python client.py <domain/ip> <port> <put filename|get filename|list>"

class FTPClient:

    def __init__(self, host, port, command):
        logging.basicConfig(filename='client.log',level=logging.DEBUG)
        self.cli_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = self.check_host(host)
        self.port = self.check_port(port)
        self.command = self.check_command(command)

        self.protocol_commands = {
            "put": self.put_file,
            "get": self.get_file,
            "list": self.show_list
        }

        self.protocol_errors = {
            "FileAlreadyExists": "File already exists in current directory",
            "FileNotFound": "File could not be found in current directory",
            "FileTooLarge": "File is too large to transfer (over 5GB in size)",
            "FileZeroSized": "File is a zero-sized file (does not contain data)",
            "FileNameTooLong": "Filename of file is too long (over 255 chars)",
            "FileIsDirectory": "File is actually a directory (folder containing files)"
        }

        self.protocol_messages = {
            "FileOkTransfer": "No existing file present, OK to create new file.",
            "FileSizeReceived": "The filesize of file being transferred has successfully been received."
        }
    
    def log(self, ctype, message):
        # Logs passed message with date and time to client.log
        date = str(datetime.datetime.now()).split(".")[0]
        line = "[%s] %s" % (ctype, message)
        logging.info("%s | %s" % (date, line))

        if ctype == "ERR":

            try:
                self.disconnect()
            except OSError:
                pass
            
            raise SystemExit("[ERR] %s" % message)
        print(line)

    @staticmethod
    def get_filesize(size_bytes):
        # Converts bytes to larger suffix
        # Returns converted filesize as a string
        sizes = ['B', 'KB', 'MB', 'GB']
        i = 0
        while size_bytes > 1024 and i < 5:
            size_bytes = size_bytes / 1024.00
            i += 1
        return "%0.2f%s" % (size_bytes, sizes[i])
    
    # Arguement Checkers
    
    def check_command(self, command):
        cmd_type = command[0].lower()

        if cmd_type not in ["list", "put", "get"]:
            self.log("ERR", "The parameter %s is not supported by this client. Try: %s" % (cmd_type, EXAMPLE_INPUT))

        if (cmd_type == "put" or cmd_type == "get") and len(command) != 2:
            self.log("ERR", "The \"%s\" command must be followed by the <filename> field. Try: %s" % (cmd_type, EXAMPLE_INPUT))

        return command

    def check_host(self, host):

        if host.lower() != "localhost" and (" " in host or not re.match(r"^[a-zA-Z0-9_.-]*$", host)):
            self.log("ERR", "The domain/IP address provided contains spaces and/or special characters. " +
                            "Allowed characters: letters, numbers, periods, dashes and underscores.")
        return host

    def check_port(self, port):

        if not port.isdigit() or not (1 <= len(port) <= 5):
            self.log("ERR", "The port parameter that has been provided is too short/long or is not a numerical value")
        if int(port) < 0:
            self.log("ERR", "The port parameter that has been provided is not a positive numerical value")

        return int(port)
    
    def start(self):
        self.log("OK!", "Client startup initialised.")

        # Parse command list and check if valid command. Also, check if command needs the parameter filename
        if self.command[0] == "list":
            self.protocol_commands[self.command[0]]()
        else:
            self.protocol_commands[self.command[0]](filename=self.command[1])
        # After command execution, notify server of disconnect and close socket on client side.
        self.disconnect()

    def connect(self):
        try:
            # Try connect to server. If connection refused, log and raise SystemExit
            self.cli_socket.connect((self.host, self.port))
            self.log("CON", "Successfully connected to server at: %s:%s" % (self.host, self.port))
        except (socket.gaierror, ConnectionRefusedError) as e:
            self.cli_socket.close()
            self.log("ERR", "An error occurred when connecting to host %s:%s\n%s" % (self.host, self.port, str(e)))
    
    def disconnect(self):
        # Notify server of disconnect, then close client.
        self.cli_socket.send(b"DISCONNECT")
        self.log("DIS", "Disconnected from server.")
    
    # Command execution
    def put_file(self, filename):

        # Check file/filename for issues
        if filename not in os.listdir(os.getcwd()):
            self.log("ERR", "FileNotFound: "+self.protocol_errors["FileNotFound"])

        elif len(filename) > 255:
            self.log("ERR", "FileNameTooLong: "+self.protocol_errors["FileNameTooLong"])

        elif os.path.isdir('%s/%s' % (os.getcwd(), filename)):
            self.log("ERR", "FileIsDirectory: "+self.protocol_errors["FileIsDirectory"])

        elif os.path.getsize(('%s/%s' % (os.getcwd(), filename))) > 5368709120:
            self.log("ERR", "FileTooLarge: "+self.protocol_errors["FileTooLarge"])

        elif os.path.getsize(('%s/%s' % (os.getcwd(), filename))) == 0:
            self.log("ERR", "FileZeroSized: "+self.protocol_errors["FileZeroSized"])
        
        # Else, send PUT request to server, w/ filename
        self.connect()
        self.log("CMD", "Invoking Server Protocol 'PUT' command with filename: %s" % filename)
        self.cli_socket.send(("PUT %s" % filename).encode()) 

        response = self.cli_socket.recv(18).decode()
        
        if response in self.protocol_errors:
            self.log("ERR", response+": "+self.protocol_errors[response])
        elif response in self.protocol_messages:
            self.log("OK!", response+": "+self.protocol_messages[response])
        
        # send filesize to server
        self.log("OK!", "File '%s' found in client directory. Sending filesize to server." % filename)
        file_size = str(os.path.getsize("%s/%s" % (os.getcwd(), filename)))
        self.cli_socket.send(file_size.encode())

        # Wait for server to respond for filesize received
        response = self.cli_socket.recv(16).decode()

        if response in self.protocol_messages:

            self.log("OK!", self.protocol_messages[response])

            # Read file and send to server in packets of 4096b
            max_size = self.get_filesize(os.path.getsize(filename))
            bytes_sent = 0

            with open('%s/%s' % (os.getcwd(), filename), 'rb') as upload_file:

                data = upload_file.read(4096)
                
                while data:
                    self.cli_socket.sendall(data)
                    bytes_sent += len(data)
                    data = upload_file.read(4096)
                    curr_size = self.get_filesize(bytes_sent)
                    print("[UPL] Uploading '%s' [%s / %s]" % (filename, curr_size, max_size), end='\r')

            self.log("UPL", "Upload Complete '%s' [%s / %s]" % (filename, curr_size, max_size))
            self.log("OK!", "Server has received file '%s' from client" % filename)

    def get_file(self, filename):
        # send GET request to server, w/ filename
        self.log("CMD", "Invoking Server Protocol 'GET' command with filename: %s" % filename)

        # If filename exists in client directory, do not continue
        if filename in os.listdir(os.getcwd()):
            self.log("ERR", "FileAlreadyExists: "+self.protocol_errors["FileAlreadyExists"]+" (client).")
        
        self.connect()
        self.cli_socket.sendall(("GET " + filename).encode())

        # If server responds with a protocol error, log and raise SystemExit
        response = self.cli_socket.recv(1024).decode()
        if response in self.protocol_errors:
            self.log("ERR", "Server response: \"%s\" - %s" % (response, self.protocol_errors[response]))
        elif response in self.protocol_messages:
            self.log("OK!", "Server response: \"%s\" - %s" % (response, self.protocol_messages[response]))

        # Else server has resonded with filesize. Continue with downloading file.
        file_size = int(response)
        bytes_collected = 0
        max_size = self.get_filesize(file_size)
        download_file = open(filename, 'wb')

        # Write downloded byte data to a file named by filename received form server.
        while bytes_collected < file_size:
            data = self.cli_socket.recv(4096)
            bytes_collected += len(data)
            current_size = self.get_filesize(bytes_collected)
            download_file.write(data)
            print("[DWN] Downloading '%s' [%s / %s]" % (filename, current_size, max_size), end='\r')
        
        # Once filesize matches the downloaded bytes we have received, close file (download complete).
        download_file.close()
        self.log("DWN", "Download Complete '%s' [%s / %s]" % (filename, current_size, max_size))
        self.log("OK!", "File saved to: %s/%s" % (os.getcwd(), filename))

    def show_list(self):
        # send LIST request to server, w/ no other parameters.
        self.log("CMD", "Invoking Server Protocol 'LIST' command.")
        self.connect()
        self.cli_socket.sendall("LIST".encode())

        # If response is empty, log and raise SystemExit. Else, print response.
        response = self.cli_socket.recv(16384)
        if response:
            self.log("OK!", "Server responded with:\n%s" % response.decode())
        else:
            self.log("ERR", "Server responded without a file list.")


if __name__ == '__main__':
    if len(sys.argv) < 4:
        raise SystemExit("[ERR] The domain/IP and port parameters are required:\n" + EXAMPLE_INPUT)
    
    client = FTPClient(host=sys.argv[1], port=sys.argv[2], command=sys.argv[3:])
    client.start()



