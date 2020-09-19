# Client Server FTP

A python client-server file transfer protocol system.

This project makes use of the python sockets library and demonstrates client-server communication.

### Features:
- File upload/download between client and server
- Client and server request logging
- Multiple server conntections through threading
### Client Commands:
- `get <filename>` - download a file from a server
- `put <filename>` - upload a file to a server
- `list` - list the available files/directories being hosted

### Usage:
```bash
# Host an FTP server and wait to recieve requests from clients
$ python server.py <port>

# Make a connection to a server (host) and send a file via passing a valid command
$ python client.py <host> <port> <command>
```
