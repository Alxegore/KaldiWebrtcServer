import socket
from queue import Queue
from time import sleep
from threading import Thread

print('eq')

def socketServer(command_queue, isStop, HOST = '', PORT = 8989):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen() #(5)
    print(f"Successfully open server {s}")
    while not isStop():
        print(f"waiting to be connected")
        conn, addr = s.accept()
    #     if data == "turn_on\r\n":
    #         print(f"Conneted")
    #         conn.send(respuesta + '\r\n')
    #     conn.close()
        with conn:
            print('Connected by', addr)
            while not isStop():
#                 print('Yay we just in while forever')
#                 command_queue = Queue() # for syntax highligt
                if(command_queue.empty()):
                    sleep(1)
                else:
                    command = command_queue.get()
                    conn.sendall(command)
                    print(f"sented {command}")
    print(f"socketServer Stopped {s}")
    #             data = conn.recv(1024)
    #             if not data: 
    #                 break
    #             else:
    #                 print(data)
    #     break
    #             data = conn.recv(1024)
    #             if not data: break
    #             conn.sendall(data)
command_queue = Queue()
isStop = False

socketServerThread = Thread(target=socketServer, args=(command_queue, lambda: isStop))
socketServerThread.start()
command_queue.put(b"Test\r\n")

