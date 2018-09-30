import numpy as np
import threading

t = []

def is_pos_def(x):
    return np.all(np.linalg.eigvals(x) > 0)

def task():
    a = np.random.rand(1000, 1000)
    print threading.current_thread(), is_pos_def(a)

for i in range(2):
    t.append(threading.Thread(target=task))
    t[i].start()
    t[i].join()
