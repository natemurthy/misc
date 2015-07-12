import concurrent.futures
import time

def countdown(n):
    while n > 0:
        n -= 1

COUNT = 80000000

start = time.time()
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
    f1 = executor.submit(countdown, COUNT/2); f1.result()
    f2 = executor.submit(countdown, COUNT/2); f2.result()
end = time.time()

print(end-start)
