#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import socket
import sys


def handleRequest(tcpSocket):
	try:
		# 1. Receive request message from the client on connection socket
		request = tcpSocket.recv(1024)
		request_message_list = request.decode().split('\r\n')
		# print(request.decode())
		print('\"', request_message_list[0], '\"', sep='', end=' ')

		# 2. Extract the path of the requested object from the message (second part of the HTTP header)
		path = request_message_list[0].split()[1].split('/')[1]

		# 3. Read the corresponding file from disk
		file = open(path, 'r')

		# 4. Store in temporary buffer

		# 5. Send the correct HTTP response error
	except ConnectionResetError:
		print(400)
		header = 'HTTP/1.1 400 Bad Request\r\n'
		content = ''
	except IndexError:
		print(500)
		# file = open('500.html', 'r')
		# content = file.read()
		# file.close()
		header = 'HTTP/1.1 500 Internal Server Error\r\n'
		content = ''
	except OSError:
		print(404)
		# file = open('404.html', 'r')
		# content = file.read()
		# file.close()
		header = 'HTTP/1.1 404 Not Found\r\n'
		content = ''

		# 6. Send the content of the file to the socket
	else:
		print(200)
		content = file.read()
		file.close()
		header = 'HTTP/1.1 200 OK\r\n'

	try:
		content_length = 'Content-Length: ' + str(len(content)) + '\r\n'
		content_type = 'Content-Type: text/html\r\n'
		respond = header + content_length + content_type + '\r\n' + content
		tcpSocket.sendall(respond.encode())
	except ConnectionResetError:
		tcpSocket.close()
		return None

	# 7. Close the connection socket
	tcpSocket.close()


def startServer(serverAddress, serverPort):
	print("\nStarting server at http://127.0.0.1:%d/\n" % serverPort)

	while True:

		# 1. Create server socket
		server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		# 2. Bind the server socket to server address and server port
		server_socket.bind((serverAddress, serverPort))

		# 3. Continuously listen for connections to server socket
		server_socket.listen()

		# 4. When a connection is accepted, call handleRequest function, passing new connection socket
		#    (see https://docs.python.org/3/library/socket.html#socket.socket.accept)
		new_connection_socket, address = server_socket.accept()
		handleRequest(new_connection_socket)

		# 5. Close server socket
		server_socket.close()


startServer("", 8000)
