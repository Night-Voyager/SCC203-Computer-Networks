from socket import *

serverName = '127.0.0.1'
serverPort = 8000
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((serverName, serverPort))
request = 'GET /index.html HTTP/1.1\r\n'
clientSocket.send(request.encode())
response = clientSocket.recv(1024)
print('From server: ', response.decode())
clientSocket.close()
