# Client Server FTP Demo using Sockets

A client-server file transfer protocol system written in Python which utilises web sockets.

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

#### Example Logging (server.log)
```log
INFO:root:2020-09-19 14:18:25 [EXI] Server closed. Goodbye!
INFO:root:2020-09-19 14:18:37 [SRV] Server initialised.
INFO:root:2020-09-19 14:18:37 [OK!] Waiting for client(s) to connect...
INFO:root:2020-09-19 14:18:40 [CON] Client [10.213.1.226 @ 41676] has connected.
INFO:root:2020-09-19 14:18:40 [CMD] Client [10.213.1.226 @ 41676] has executed command: PUT test.txt.
WARNING:root:2020-09-19 14:18:40 [ERR] FileAlreadyExists: File already exists in current directory (client).
INFO:root:2020-09-19 14:18:40 [DIS] Client [10.213.1.226 @ 41676] has disconnected.```
