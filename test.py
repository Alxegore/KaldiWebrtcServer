import numpy as np

command = list()
with open('command.txt', 'r') as file:
    for line in file:
         command.append(line.strip().split())
        
words = set()
for cmd in command:
    for w in cmd:
        words.add(w)

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
    mn = np.inf
    best_match = ''
    for cmd in all_command:
        distance = DTW(cmd, test)
        if mn > distance:
            mn = distance
            best_match = cmd
    return best_match, distance

t = 'โอม เดิน หน้า \r'.split(' ')
b, d = find_best_match(t, command)
print('test :', t)
print('predict :', (' ').join(b))