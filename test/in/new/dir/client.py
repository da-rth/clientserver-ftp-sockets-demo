import socket
import sys
import select

"""
Client.py
Author: 2086380A
NOSE 2 - Assessment 1

Requires parameters: <hostname> <port> <put filename | get filename | list>
"""


def check_argv():
    if len(sys.argv) < 4:
        raise SystemExit(
            "\nThe hostname and port parameters are required:"
            "\nTry:     python client.py <hostname/ip> <port> <parameter>"
            "\nExample: python client.py  127.0.0.1     8080   list"
        )

    if sys.argv[3].lower() not in ["list", "put", "get"]:
        raise SystemExit(
            "\nThe parameter \"%s\" is not supported. Try:"
            "\npython client.py <hostname/ip> <port> <put filename | get filename | list>" % sys.argv[3]
        )

    if (not (1 <= len(sys.argv[2]) <= 5)) or (not sys.argv[2].isdigit()):
        raise SystemExit(
            "\nThe port parameter that has been provided is too short/long or is not a numerical value."
        )

    if (sys.argv[3] == "put" or sys.argv[3] == "get") and len(sys.argv) != 5:
        raise SystemExit(
            "\nThe \"%s\" command must be followed by the <filename> field."
            "\nExample: python client.py <hostname/ip> <port> %s /path/to/my/file.txt" % (sys.argv[3], sys.argv[3])
        )


def put_file(clisock):
    # connect to socket
    filename = sys.argv[4]
    print("[CMD] Invoking Server Protocol 'PUT' command with filename: %s" % filename)

    data = open(filename, 'rb').read()
    clisock.send(data)

    # await response
    # data = cli_sock.recv(1024)
    # print(data.decode('utf'))


def get_file(clisock):
    # connect to socket, connect to server and download from server
    filename = sys.argv[4]

    print("[CMD] Invoking Server Protocol 'GET' command with filename: %s" % filename)

    clisock.sendall(str("get " + filename).encode('utf'))

    while True:
        f = open(filename, 'wb')
        data = clisock.recv(4096)
        while data:
            f.write(data)
            if len(data) < 4096:
                break
            else:
                data = clisock.recv(4096)
        f.close()
        break
    print("end")



    
    print('Successfully get the file')

    print("Download Completed")


def show_list(clisock):
    # connect to socket, print list of files
    print("[CMD] Invoking Server Protocol 'LIST' command.")
    clisock.sendall("list".encode('utf'))
    data = cli_sock.recv(4096)
    print(data.decode('utf') if data else '[ERR] No returned data in response.')


commands = {
    "put": put_file,
    "get": get_file,
    "list": show_list
}

if __name__ == '__main__':

    check_argv()
    host = sys.argv[1]
    port = int(sys.argv[2])
    cmd = sys.argv[3].lower()
    cli_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        cli_sock.connect((host, port))
    except socket.gaierror:
        cli_sock.close()
        raise SystemExit("[ERR] Could not connect to host '%s' at port: %s" % (host, port))

    commands[cmd](cli_sock)



