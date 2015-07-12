import time
start = time.time()
print("\n(Map) multiplying 32 million elements by 2")
dbls=map(lambda n: 2*n, range(32000000))
print("(Reduce) sum: %d" % sum(dbls))
end = time.time()
print("Total MapReduce time: %f" % (end-start))
