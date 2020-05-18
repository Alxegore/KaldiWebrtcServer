import socket
from queue import Queue
from time import sleep
from threading import Thread

print('eq')

HOST = '127.0.0.1'  # The server's hostname or IP address
PORT = 8989        # The port used by the server

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(b'Hello, world')
    while True:
        data = s.recv(1024)
        print('Received', repr(data))

