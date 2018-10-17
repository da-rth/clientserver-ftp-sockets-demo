import socket
import sys

"""
Server.py
Author: 2086380A
NOSE 2 - Lab 3
Client & Server with Socket
"""

address = "127.0.0.1"
port = 8080

if __name__ == '__main__':

    cli_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cli_sock.connect((address, port))

    while cli_sock:

        message = input('>> ')

        if message.lower() == 'exit':
            cli_sock.close()
            print("Goodbye!")
            sys.exit()
        else:
            cli_sock.sendall(message.encode())
            data = cli_sock.recv(1024)
            print(data.decode('utf'))
