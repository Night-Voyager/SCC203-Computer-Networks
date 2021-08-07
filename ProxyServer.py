#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import select
import socket
import sys


def handleRequest(tcpSocket):
    # 1. Receive request message from the client on connection socket
    request = tcpSocket.recv(1024)
    print(request.decode())
    request_message_list = request.decode().split('\r\n')
    print(request_message_list)

    # 2. Extract the path of the requested host from the message
    host = request_message_list[0].split()[1].split('/')[2]
    print(host)

    # 3. Look up hostname, resolving it to an IP address
    destinationAddress = socket.gethostbyname(host)

    # 4. Create socket
    destinationPort = 80
    destinationSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    destinationSocket.connect((destinationAddress, destinationPort))

    # 5. Forward the client’s request to the server, and deliver the response generated from the server to the client
    destinationSocket.send(request)

    wait = select.select([destinationSocket], [], [], 1)
    if not wait[0]:
        tcpSocket.close()
        return

    response = destinationSocket.recv(1024)
    print(response.decode())
    tcpSocket.sendall(response)

    # 6. Close socket
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
