'''
    execute `pip install comtool --upgrade` first
    Then run a TCP server on COMTool
    Finally run this script to connect the server and send data
'''
from COMTool.plugins import graph_protocol
import math
import socket
import time

class Conn:
    def __init__(self, addr, port):
        self.addr = addr
        self.port = port
        self.sock = None
        # connect tcp server
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.addr, self.port))

    def send(self, data):
        self.sock.send(data)

if __name__ == "__main__":
    conn = Conn("127.0.0.1", 2345)

    count = 0
    while 1:
        # x belong to [0, 2pi]
        x = count * 2 * math.pi / 100
        y = math.sin(x)
        frame1 = graph_protocol.plot_pack("data1", x, y, header= b'\xAA\xCC\xEE\xBB')
        y = math.pow(math.cos(x), 2)
        frame2 = graph_protocol.plot_pack("data2", x, y, header= b'\xAA\xCC\xEE\xBB')
        conn.send(frame1)
        conn.send(frame2)
        count += 1
        time.sleep(0.1)
