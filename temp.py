import socket
from queue import Queue
from time import sleep
from threading import Thread
from flask import Flask, request, render_template, redirect, url_for, jsonify, abort
from flask_cors import CORS
command_queue = Queue()

initial = False

def socketServer(command_queue, isStop, HOST = '', PORT = 8989):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print(PORT)
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

def init():
  print('init jaa')
  isStop = False
  socketServerThread = Thread(target=socketServer, args=(command_queue, lambda: isStop))
  socketServerThread.start()

app = Flask(__name__)
# cors = CORS(app)
@app.route('/')
def index():
    init()
    return 'index'

@app.route('/predict', methods=['POST'])
def predict():
    text = request.json['text']
    print('txt', text, bytes(text, encoding='utf-8'))
    command_queue.put(bytes(text, encoding='utf-8'))
    return jsonify({'predict': text})

if __name__ == '__main__':
    app.run(host='localhost', port=8888,debug=True)
