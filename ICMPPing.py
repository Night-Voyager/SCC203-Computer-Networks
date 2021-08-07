#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import socket
import os
import sys
import struct
import time
import select
import binascii

ICMP_ECHO_REQUEST = 8  # ICMP type code for echo request messages
ICMP_ECHO_REPLY = 0  # ICMP type code for echo reply messages

NETWORK_UNREACHABLE = 0  # ICMP error code for network unreachable error
HOST_UNREACHABLE = 1  # ICMP error code for host unreachable error


def icmpErrorHandler(type, code):
    if type == 3:
        if code == NETWORK_UNREACHABLE:
            print("Destination Network Unreachable")
        elif code == HOST_UNREACHABLE:
            print("Destination Host Unreachable")


def checksum(string):
    csum = 0
    countTo = (len(string) // 2) * 2
    count = 0

    while count < countTo:
        thisVal = string[count + 1] * 256 + string[count]
        csum = csum + thisVal
        csum = csum & 0xffffffff
        count = count + 2

    if countTo < len(string):
        csum = csum + string[len(string) - 1]
        csum = csum & 0xffffffff

    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)

    answer = socket.htons(answer)

    return answer


def receiveOnePing(icmpSocket, destinationAddress, ID, timeout):
    # 1. Wait for the socket to receive a reply
    wait = select.select([icmpSocket], [], [], timeout)

    # 2. Once received, record time of receipt, otherwise, handle a timeout
    receiveTime = time.time()

    if not wait[0]:  # timeout
        return -1, 0, None, None

    # 3. Compare the time of receipt to time of sending, producing the total network delay
    receivePacket = icmpSocket.recv(1024)
    sendTime = struct.unpack('d', receivePacket[28:36])[0]
    delay = receiveTime - sendTime

    # 4. Unpack the packet header for useful information, including the ID
    header = receivePacket[20:28]
    type, code, sum, receiveID, sequence = struct.unpack('bbHHh', header)

    TTL = struct.unpack('b', receivePacket[8:9])[0]

    # 5. Check that the ID matches between the request and reply
    # print(ID == receiveID)

    # 6. Return total network delay
    return delay, TTL, type, code


def sendOnePing(icmpSocket, destinationAddress, ID):
    # 1. Build ICMP header
    type = ICMP_ECHO_REQUEST
    code = 0
    sum = 0
    sequence = 0

    header = struct.pack('bbHHh', type, code, sum, ID, sequence)
    data = struct.pack('d', time.time())

    # 2. Checksum ICMP packet using given function
    packet = header + data
    sum = checksum(packet)

    # 3. Insert checksum into packet
    header = struct.pack('bbHHh', type, code, sum, ID, sequence)
    packet = header + data

    # 4. Send packet using socket
    icmpSocket.connect((destinationAddress, 12000))
    icmpSocket.send(packet)

    # 5. Record time of sending
    # Not necessary


def doOnePing(destinationAddress, timeout):
    # 0. Get the process ID
    ID = os.getpid()

    # 1. Create ICMP socket
    icmpSocket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname('icmp'))

    # 2. Call sendOnePing function
    sendOnePing(icmpSocket, destinationAddress, ID)

    # 3. Call receiveOnePing function
    delay, TTL, type, code = receiveOnePing(icmpSocket, destinationAddress, ID, timeout)

    # 4. Close ICMP socket
    icmpSocket.close()

    # 5. Return total network delay
    return delay, TTL, type, code


def ping(host, timeout=1, count=4):
    # 1. Look up hostname, resolving it to an IP address
    ipAddress = socket.gethostbyname(host)

    # 2. Call doOnePing function, approximately every second
    # 3. Print out the returned delay
    # 4. Continue this process until stopped
    if ipAddress == host:
        print("\nPinging %s with 8 bytes of data:" % host)
    else:
        print("\nPinging %s [%s] with 8 bytes of data:" % (host, ipAddress))

    time_list = []
    for i in range(count):
        delay, TTL, type, code = doOnePing(ipAddress, timeout)
        if delay == -1:
            print("Request timed out.")
        else:
            time_list.append(delay*1000)
            print("Reply from %s: bytes=8 time=%dms TTL=%d" % (ipAddress, delay*1000, TTL))
            icmpErrorHandler(type, code)
        time.sleep(1)

    print("\nPing statistics for %s:\n"
          "\tPackets: Sent = %d, Received = %d, Lost = %d (%d%% loss),"
          % (ipAddress, count, len(time_list), count - len(time_list), ((count - len(time_list)) / count * 100)))

    if time_list:
        print("\nApproximate round trip times in milli-seconds:\n"
              "\tMinimum = %dms, Maximum = %dms, Average = %dms"
              % (min(time_list), max(time_list), sum(time_list) / len(time_list)))


if __name__ == '__main__':
    ping("lancaster.ac.uk")
