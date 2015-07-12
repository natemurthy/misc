from multiprocessing import Process
import time

def countdown(n):
    while n > 0:
    	n -= 1
    	
COUNT = 80000000

p1 = Process(target=countdown, args=(COUNT/2,))
p2 = Process(target=countdown, args=(COUNT/2,))

start = time.time()
p1.start(); p2.start()
p1.join(); p2.join()
end = time.time()

print(end-start)
