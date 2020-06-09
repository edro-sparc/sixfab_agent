import socket
import struct
import sys
import time

def get_utc0(addr='uk.pool.ntp.org'):
    REF_TIME_1970 = 2208988800
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    data = '\x1b' + 47 * '\0'
    client.settimeout(1)
    client.sendto(data.encode(), (addr, 123))
    data, _ = client.recvfrom(1024)
    if data:
        t = struct.unpack('!12I', data)[10]
        t -= REF_TIME_1970
        return t