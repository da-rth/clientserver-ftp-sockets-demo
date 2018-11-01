# Networks & Operating Systems Essentials 2 - Assessed Exercise 1  | Command 
| Usage | |--|--| | LIST | Returns a list of files in server directory | | 
PUT **filename** | Uploads specified file to server directory from client.| | 
GET **filename** | Downloads specified file from server directory to client.|   
Run the server: ```sh cd server python3 server.py <PORT> ``` Then execute a 
command with the client: ```sh cd client python3 client.py <IP/HOST> <PORT> 
<list|put filename|get filename> ``` Python Version: 
[Python3](https://www.python.org/download/releases/3.0/)
