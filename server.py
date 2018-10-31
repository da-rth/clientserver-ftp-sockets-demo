import os
import sys
import socket
import select
import threading
import logging
import datetime

#TODO: Send filelist in parts if over 4096bytes
#TODO: Check if filesize of file being sent/received is larger than 5gb
#TODO: Check if filename of file is too long (longer than 256chars?)
#TODO: Add subdirectory support?

class FTPServer(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        logging.basicConfig(filename='server.log',level=logging.DEBUG)
        self.dir = os.getcwd()
        self.port = self.check_args_port()
        self.public_ip = self.get_ip_address()
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
        self.protocol_errors = {
            "FileAlreadyExists": "File already exists in current directory (cannot be over-written)",
            "FileNotFound": "File could not be found in client directory",
            "FileTooLarge": "File is too large to transfer (over 5GB in size)",
            "FileZeroSized": "File is a zero-sized file (does not contain data)",
            "FileNameTooLong": "Filename of file is too long (over 255 chars)",
            "FileIsDirectory": "File is actually a directory (folder containing files)"
        }

        self.protocol_messages = {
            "FileOK": "No existing file present, OK to create new file.",
            "FileSizeReceived": "The filesize of file being transferred has successfully been received."
        }
    
    @staticmethod
    def clear_terminal():
        os.system('clear' if os.name != 'nt' else 'cls')
    
    @staticmethod
    def check_args_port():
        if len(sys.argv) < 2:
            raise SystemExit("[ERR] Port number expected.")

        port = sys.argv[1]

        if (not (1 <= len(port) <= 5)) or (not port.isdigit()):
            raise SystemExit("[ERR] Port must be a numerical value and between 0-99999.")
        else:
            return int(port)
    
    @staticmethod
    def get_ip_address():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip_address = s.getsockname()[0]
        except socket.gaierror:
            ip_address = "127.0.0.1"
        finally:
            s.close()
        return ip_address
    
    def log(self, ctype, message):
        date = str(datetime.datetime.now()).split(".")[0]
        line = "[%s] %s" % (ctype, message)

        if ctype == "ERR":
            logging.warning("%s %s" % (date, line))
            print(line)

        elif ctype == "SRV":
            logging.info("\n%s %s" % (date, line))
            print(line)
        
        else:
            logging.info("%s %s" % (date, line))
            print(line)
        
    # Commands
    def list_files(self):
        ip, port = self.current_conn['address']
        self.log("CMD", "Client [%s @ %s] has executed command: LIST." % (ip, port))

        files_dirs = os.listdir(self.dir)
        file_list = "\n".join([" - [DIR] "+file if os.path.isdir(file) else " - [FIL] "+file for file in files_dirs])

        self.current_conn['socket'].sendall(file_list.encode('utf'))
        self.log("OK!", "Client [%s @ %s] has received full file list." % (ip, port))

    def send_file(self):
        ip, port = self.current_conn['address']
        filename = self.current_conn['command'][1]

        self.log("CMD", "Client [%s @ %s] has executed command: GET %s" % (ip, port, filename))

        # Check file/filename for security/file issues
        if filename not in os.listdir(os.getcwd()):
            self.current_conn['socket'].sendall(b"FileNotFound")
            self.log("ERR", "FileNotFound: "+self.protocol_errors["FileNotFound"])
        
        elif len(filename) > 255:
            self.current_conn['socket'].sendall(b"FileNameTooLong")
            self.log("ERR", "FileNameTooLong: "+self.protocol_errors["FileNameTooLong"])
        
        elif os.path.isdir('%s/%s' % (os.getcwd(), filename)):
            self.current_conn['socket'].sendall(b"FileIsDirectory")
            self.log("ERR", "FileIsDirectory: "+self.protocol_errors["FileIsDirectory"])
        
        elif os.path.getsize(('%s/%s' % (os.getcwd(), filename))) > 5368709120:
            self.current_conn['socket'].sendall(b"FileTooLarge")
            self.log("ERR", "FileTooLarge: "+self.protocol_errors["FileTooLarge"])
        
        elif os.path.getsize(('%s/%s' % (os.getcwd(), filename))) == 0:
            self.current_conn['socket'].sendall(b"FileZeroSized")
            self.log("ERR", "FileZeroSized: "+self.protocol_errors["FileZeroSized"])
        
        else:
            self.log("OK!", "File '%s' found in server directory. Sending client total file-size." % filename)
            
            # send client the filesize of file being sent.
            filesize = str(os.path.getsize(self.dir+'/'+filename))
            self.current_conn['socket'].sendall(filesize.encode())

            upload = open(self.dir+'/'+filename, 'rb')
            data = upload.read(4096)
            
            while data:
                self.current_conn['socket'].sendall(data)
                data = upload.read(4096)
            
            self.log("OK!", "Client [%s @ %s] has downloaded file '%s' from server." % (ip, port, filename))

    def save_file(self):
        
        ip, port = self.current_conn['address']
        filename = self.current_conn['command'][1]
        self.log("CMD", "Client [%s @ %s] has executed command: PUT %s." % (ip, port, filename))
        
        if filename in os.listdir(os.getcwd()):
            self.log("ERR", "FileAlreadyExists: "+self.protocol_errors["FileAlreadyExists"])
            self.current_conn['socket'].send(b"FileAlreadyExists")
            return
        else:
            self.log("OK!", "FileOK: "+self.protocol_messages["FileOK"])
            self.current_conn['socket'].send(b"FileOK")
        
        response = self.current_conn['socket'].recv(1024).decode()
        file_size = int(response)

        self.current_conn['socket'].sendall(b"FileSizeReceived")
        self.log("OK!", "FileSizeReceived: "+self.protocol_messages["FileSizeReceived"])

        with open(filename, 'wb') as download_file:
           
            bytes_collected = 0

            while bytes_collected < file_size:
                data = self.current_conn['socket'].recv(4096)
                bytes_collected += len(data)
                download_file.write(data)

            self.log("OK!", "Client upload complete. File saved to: %s/%s" % (self.dir, filename))

    def disconnect(self, conn):
        try:
            self.log("DIS", "Client [%s @ %s] has disconnected." % conn.getpeername())
            conn.close()
            self.conns.remove(conn)
        except socket.error:
            pass
    
    def loop_socket_check(self):

        while self.server_is_running:

            # Using select.select to obtain the read ready sockets in the connections list (self.conns)
            read_connections = select.select(self.conns, [], [], 30)[0]

            for connection in read_connections:

                if connection == self.srv_socket:
                    try:
                        cli_sock, (ip, port) = self.srv_socket.accept()
                        self.conns.append(cli_sock)
                        self.log("CON", "Client [%s @ %s] has connected." % (ip, port))
                    except socket.error:
                        break
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

                    except socket.error as e:
                        self.log("ERR", str(e))
                        self.disconnect(connection)

    def start(self):

        self.clear_terminal()

        print(
            "\nLaunching server at:"
            "\n- IP: %s"
            "\n- Port: %s"
            "\n- Directory: %s"
            "\n- Server Log: server.log"
            "\n" % (self.public_ip, self.port, self.dir)
        )

        # Create socket and add to connections list
        self.srv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.srv_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.srv_socket.bind(('', self.port))
        self.srv_socket.listen(10)

        # Add server socket to list of connections and set running to True
        self.conns.append(self.srv_socket)
        self.server_is_running = True

        self.log("SRV", "Server initialised.")
        self.log("OK!", "Waiting for client(s) to connect...")
        print()

        try:
            # Begin waiting for/looping through socket connections
            self.loop_socket_check()
        except KeyboardInterrupt:
            # If user presses CTRL+C, catch interrupt and print message. 
            # Interrupt is sometimes delayed...
            self.server_is_running = False
            self.log("EXI", "Server closed. Goodbye!")
        finally:
            self.srv_socket.close()


if __name__ == '__main__':
    server = FTPServer()
    server.start()
