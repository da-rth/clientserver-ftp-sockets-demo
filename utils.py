import sys
import os
import socket

# Utilities


def clear_terminal():
    os.system('clear' if os.name != 'nt' else 'cls')


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