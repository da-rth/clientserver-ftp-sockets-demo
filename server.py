import os
import sys
import socket
import select
import threading
import logging
import datetime

#TODO: Send filelist in parts if over 4096bytes


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

        if type == "ERR":
            logging.warning("%s %s" % (date, line))

        elif type == "SRV":
            logging.info("\n%s %s" % (date, line))
            print(line)
        else:
            logging.info("%s %s" % (date, line))
            print(line)
        
    # Commands
    def list_files(self):
        ip, port = self.current_conn['address']
        self.log("CMD", "Client [%s:%s] has executed command: LIST." % (ip, port))

        files_dirs = os.listdir(self.dir)
        file_list = "\n".join([" - [DIR] "+file if os.path.isdir(file) else " - [FIL] "+file for file in files_dirs])

        self.current_conn['socket'].sendall(file_list.encode('utf'))
        self.log("OK!", "Client [%s:%s] has received full file list." % (ip, port))

    def send_file(self):
        ip, port = self.current_conn['address']
        filename = self.current_conn['command'][1]

        self.log("CMD", "Client [%s:%s] has executed command: GET %s" % (ip, port, filename))

        if filename not in os.listdir(self.dir):
            self.current_conn['socket'].sendall("FileNotFound".encode('utf'))
            self.log("ERR", "File '%s' could not be found in server directory. Notifying client." % filename)
        
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
            
            self.log("OK!", "Client [%s:%s] has downloaded file '%s' from server." % (ip, port, filename))

    def save_file(self):
        ip, port = self.current_conn['address']
        filename = self.current_conn['command'][1]

        self.log("CMD", "Client [%s:%s] has executed command: PUT %s." % (ip, port, filename))
        response = self.current_conn['socket'].recv(1024)
        response = response.decode()

        if response == "FileNotFound":
            self.log("ERR", "Client response: %s - '%s' does not exist in current client directory." % (response, filename))
            return
        
        file_size = int(response)
        self.current_conn['socket'].sendall("RECEIVED".encode())
        
        self.log("OK!", "Recieved file size for '%s' from server: %s." % (filename, file_size))

        with open(filename, 'wb') as download_file:
            data = self.current_conn['socket'].recv(4096)
            bytes_collected = 0

            while data and (bytes_collected < file_size):
                bytes_collected += len(data)
                download_file.write(data)
                if len(data) < 4096:
                    break
                data = self.current_conn['socket'].recv(4096)

            self.log("OK!", "Client upload complete. File saved to: %s/%s" % (self.dir, filename))

    def disconnect(self, conn):
        try:
            self.log("DIS", "Client [%s:%s] has disconnected." % conn.getpeername())
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
                        self.log("CON", "Client [%s:%s] has connected." % (ip, port))
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
                        print(e)
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

        self.conns.append(self.srv_socket)
        self.server_is_running = True

        self.log("SRV", "Server initialised.")
        self.log("OK!", "Waiting for client(s) to connect...")
        print()

        try:
            self.loop_socket_check()
        except KeyboardInterrupt:
            self.server_is_running = False
            self.log("EXI", "Server closed. Goodbye!")
        finally:
            self.srv_socket.close()


if __name__ == '__main__':
    server = FTPServer()
    server.start()
