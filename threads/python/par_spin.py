from threading import Thread
from subprocess import Popen
import time
 
def countdown(n):
    while n > 0:
        n -= 1
 
COUNT = 50000000
 
p = Popen(['python','spin.py'])
t1 = Thread(target=countdown, args=(COUNT/2,))
t2 = Thread(target=countdown, args=(COUNT/2,))
 
start = time.time()
t1.start(); t2.start()
t1.join(); t1.join()
end = time.time()
p.terminate()
 
print(end-start)
