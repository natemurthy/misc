import time
start = time.time()
print("\n(Map) multiplying 32 million elements by 2")
dbls=[2*n for n in range(32000000)]
print("(Reduce) sum: %d" % sum(dbls))
end = time.time()
print("Total MapReduce time: %f" % (end-start))
