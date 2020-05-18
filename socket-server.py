import socket
from queue import Queue
from time import sleep
from threading import Thread
from flask import Flask, request, render_template, redirect, url_for, jsonify, abort
from flask_cors import CORS, cross_origin
import numpy as np

app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

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
        with conn:
            print('Connected by', addr)
            while not isStop():
                if(command_queue.empty()):
                    sleep(1)
                else:
                    command = command_queue.get()
                    conn.sendall(command)
                    print(f"sented {command}")
    print(f"socketServer Stopped {s}")

def dist(x, y):
    if x == y: return 0
    elif x[0] == y[0]: return abs(len(x) - len(y)) / (len(x) + len(y)) * 0.25 + 0.5
    else: return abs(len(x) - len(y)) / (len(x) + len(y)) * 0.5 + 0.5

def DTW(s1, s2):
    arr = np.zeros((len(s1) + 1, len(s2) + 1))
    arr[:, :] = np.inf
    for i in range(1, len(s1) + 1):
        for j in range(1, len(s2) + 1):
            row = i - 1
            col = j - 1
            if i == 1 and j == 1:
                arr[i, j] = dist(s1[row], s2[col])
                continue
                
            arr[i, j] = min(arr[i, j-1] + dist(s1[row],s2[col]),\
                            arr[i-1, j-1] + 2*dist(s1[row],s2[col]),\
                            arr[i-1, j] + dist(s1[row],s2[col]))
    
    return arr[-1, -1]

def find_best_match(test , all_command):
    print('begin to find', test)
    mn = np.inf
    best_match = ''
    for cmd in all_command:
        distance = DTW(cmd, test)
        if mn > distance:
            mn = distance
            best_match = cmd
    return best_match, distance

command = list()
translate_command = {}
def init():
  with open('command.txt', 'r') as file:
      for line in file:
          command.append(line.strip().split())
  with open('translate.txt', 'r') as file:
      idx = 0
      for line in file:
          print((' ').join(command[idx]))
          translate_command[(' ').join(command[idx])] = line.strip()
          idx += 1
  isStop = False
  socketServerThread = Thread(target=socketServer, args=(command_queue, lambda: isStop))
  socketServerThread.start()

@app.route('/')
def index():
    init()
    return 'index'

@app.route('/predict', methods=['POST'])
@cross_origin(origin='localhost')
def predict():
    text = request.json['text']
    print(text)
    t = text.split(' ')
    b, d = find_best_match(t[:len(t)-1], command)
    print('predict :', (' ').join(b))
    print('translate :', translate_command[(' ').join(b)])

    command_queue.put(bytes(translate_command[(' ').join(b)], encoding='utf-8'))
    return jsonify({'predict': text})

if __name__ == '__main__':
    app.run(host='localhost', port=8888,debug=True)
