from .base import ConnectionStatus
from .conn_serial import Serial
from .conn_tcp_udp import TCP_UDP
from .conn_ssh import SSH

conns = [Serial, TCP_UDP, SSH]
