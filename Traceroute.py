#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import socket
import os
import sys
import struct
import time
import select
import binascii


def icmpTypeCodeHanlder(type, code):
    if type == 0:
        if code == 0:
            return "Echo Reply"  # 回显应答（Ping应答）
    elif type == 3:
        if code == 0:
            return "Network Unreachable"  # 网络不可达
        elif code == 1:
            return "Host Unreachable"  # 主机不可达
        elif code == 2:
            return "Protocol Unreachable"  # 协议不可达
        elif code == 3:
            return "Port Unreachable"  # 端口不可达
        elif code == 4:
            return "Fragmentation needed but no frag. bit set"  # 需要进行分片但设置不分片比特
        elif code == 5:
            return "Source routing failed"  # 源站选路失败
        elif code == 6:
            return "Destination network unknown"  # 目的网络未知
        elif code == 7:
            return "Destination host unknown"  # 目的主机未知
        elif code == 8:
            return "Source host isolated (obsolete)"  # 源主机被隔离（作废不用）
        elif code == 9:
            return "Destination network administratively prohibited"  # 目的网络被强制禁止
        elif code == 10:
            return "Destination host administratively prohibited"  # 目的主机被强制禁止
        elif code == 11:
            return "Network unreachable for TOS"  # 由于服务类型TOS，网络不可达
        elif code == 12:
            return "Host unreachable for TOS"  # 由于服务类型TOS，主机不可达
        elif code == 13:
            return "Communication administratively prohibited by filtering"  # 由于过滤，通信被强制禁止
        elif code == 14:
            return "Host precedence violation"  # 主机越权
        elif code == 15:
            return "Precedence cutoff in effect"  # 优先中止生效
    elif type == 4:
        if code == 0:
            return "Source quench"  # 源端被关闭（基本流控制）
    elif type == 5:
        if code == 0:
            return "Redirect for network"  # 对网络重定向
        elif code == 1:
            return "Redirect for host"  # 对主机重定向
        elif code == 2:
            return "Redirect for TOS and network"  # 对服务类型和网络重定向
        elif code == 3:
            return "Redirect for TOS and host"  # 对服务类型和主机重定向
    elif type == 8:
        return "Echo request"  # 回显请求（Ping请求）
    elif type == 9:
        return "Router advertisement"  # 路由器通告
    elif type == 10:
        return "Route solicitation"  # 路由器请求
    elif type == 11:
        if code == 0:
            return "TTL equals 0 during transit"  # 传输期间生存时间为0
        elif code == 1:
            return "TTL equals 0 during reassembly"  # 在数据报组装期间生存时间为0
    elif type == 12:
        if code == 0:
            return "IP header bad (catchall error)"  # 坏的IP首部（包括各种差错）
        elif code == 1:
            return "Required options missing"  # 缺少必需的选项
    elif type == 13:
        return "Timestamp request (obsolete)"  # 时间戳请求（作废不用）
    elif type == 14:
        return "Timestamp reply (obsolete)"  # 时间戳应答（作废不用）
    elif type == 15:
        return "Information request (obsolete)"  # 信息请求（作废不用）
    elif type == 16:
        return "Information reply (obsolete)"  # 信息应答（作废不用）
    elif type == 17:
        return "Address mask request"  # 地址掩码请求
    elif type == 18:
        return "Address mask reply"  # 地址掩码应答


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


def receiveOnePing(tracerouteSocket, destinationAddress, ID, timeout):
    # 1. Wait for the socket to receive a reply
    wait = select.select([tracerouteSocket], [], [], timeout)

    # 2. Once received, record time of receipt, otherwise, handle a timeout
    receiveTime = time.time()

    if not wait[0]:  # timeout
        return -1, -1, -1, None

    # 3. Compare the time of receipt to time of sending, producing the total network delay
    receivePacket, receiveAddress = tracerouteSocket.recvfrom(1024)

    # 4. Unpack the packet header for useful information, including the ID
    header = receivePacket[20:28]
    type, code, sum, receiveID, sequence = struct.unpack('bbHHh', header)

    # TTL = struct.unpack('b', receivePacket[8:9])[0]

    # 5. Check that the ID matches between the request and reply
    # print(ID == receiveID)

    # 6. Return total network delay
    return receiveTime, type, code, receiveAddress[0]


def sendOnePing(tracerouteSocket, destinationAddress, ID):
    # 1. Build header
    type = 8
    code = 0
    sum = 0
    sequence = 0

    header = struct.pack('bbHHh', type, code, sum, ID, sequence)
    data = struct.pack('d', time.time())

    # 2. Checksum packet using given function
    packet = header + data
    sum = checksum(packet)

    # 3. Insert checksum into packet
    header = struct.pack('bbHHh', type, code, sum, ID, sequence)
    packet = header + data

    # 4. Send packet using socket
    # tracerouteSocket.connect((destinationAddress, 12000))
    # tracerouteSocket.send(packet)
    tracerouteSocket.sendto(packet, (destinationAddress, 12000))

    # 5. Record time of sending
    return time.time()


def doOnePing(destinationAddress, timeout, protocal, TTL):
    # 0. Get the process ID
    ID = os.getpid()

    # 1. Create a socket
    tracerouteSocket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname(protocal))
    tracerouteSocket.setsockopt(socket.SOL_IP, socket.IP_TTL, TTL)

    # 2. Call sendOnePing function
    sendTime = sendOnePing(tracerouteSocket, destinationAddress, ID)

    # 3. Call receiveOnePing function
    receiveTime, type, code, receiveAddress = receiveOnePing(tracerouteSocket, destinationAddress, ID, timeout)

    # 4. Close socket
    tracerouteSocket.close()

    # 5. Return total network delay
    msg = icmpTypeCodeHanlder(type, code)
    if msg == "TTL equals 0 during transit" or msg == "Echo Reply":
        delay = (receiveTime - sendTime) * 1000
        if delay < 1:
            print("  <1 ms", end="  ")
        else:
            print("%4d ms" % delay, end="  ")
        return True, receiveAddress
    elif type == -1 and code == -1:
        print("   *   ", end="  ")
        return False, "Request timed out."
    else:
        print("   *   ", end="  ")
        return False, msg


def doThreePings(destinationAddress, timeout, protocal, TTL):
    isNormal = False
    returnAddress = ""
    errorMsg = ""

    for i in range(3):
        returnCode, msg = doOnePing(destinationAddress, timeout, protocal, TTL)
        if returnCode:
            returnAddress = msg
        else:
            errorMsg = msg
        isNormal = isNormal or returnCode

    if isNormal:
        return returnAddress
    else:
        return errorMsg


def traceroute(host, timeout=1, protocal='icmp'):
    # 1. Look up hostname, resolving it to an IP address
    ipAddress = socket.gethostbyname(host)

    # 2. Call doOnePing function, approximately every second
    # 3. Print out the returned delay
    # 4. Continue this process until stopped
    if ipAddress == host:
        print("\nTracing route to %s over a maximum of 30 hops:\n" % host)
    else:
        print("\nTracing route to %s [%s]\nover a maximum of 30 hops:\n" % (host, ipAddress))

    for i in range(1, 31):
        print("%2d" % i, end='\t')
        returnAddress = doThreePings(ipAddress, timeout, protocal, i)
        try:
            returnHost = socket.gethostbyaddr(returnAddress)[0]
        except Exception as error:
            print(returnAddress)
            # print(error)
        else:
            print("%s [%s]" % (returnHost, returnAddress))
        if returnAddress == ipAddress:
            break

    print("\nTrace complete.")


traceroute("lancaster.ac.uk")
