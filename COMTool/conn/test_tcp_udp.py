import sys, os
path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..")
sys.path.insert(0, path)

from conn_tcp_udp import TCP_UDP

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    from base import ConnectionStatus

    app = QApplication(sys.argv)

    conn = TCP_UDP()
    conn.onInit({})

    class Event():
        def __init__(self, conn) -> None:
            self.conn = conn

        def onReceived(self, data):
            print("-- received:", data)
            # self.conn.send(data)

        def onConnection(self, status, msg):
            print("-- onConnection:", status, msg)
            if status == ConnectionStatus.CONNECTED:
                print("== send data")
                self.conn.send('''GET http://example.com HTTP/1.1
Accept-Language: zh-cn
User-Agent: comtool
Host: example.com:80
Connection: close

'''.encode())

        def onHint(self, level, title, msg):
            print(level, title, msg)

    event = Event(conn)

    conn.onReceived = event.onReceived
    conn.onConnectionStatus.connect(event.onConnection)
    conn.hintSignal.connect(event.onHint)
    window = conn.onWidget()
    conn.onUiInitDone()
    window.show()
    ret = app.exec_()
