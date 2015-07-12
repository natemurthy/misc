from concurrent.futures import ProcessPoolExecutor, wait
from multiprocessing import cpu_count
import sys, time

def factorize(number, factors=[]):
    for n in range(2,number+1):
        if number % n == 0:
            return factorize(number//n, factors+[n])
    return factors

workers = cpu_count()
pool = ProcessPoolExecutor(max_workers=workers)
N = int(sys.argv[1])
start = time.time(); result = pool.map(factorize, range(100, N)); end = time.time()
print (end-start)
