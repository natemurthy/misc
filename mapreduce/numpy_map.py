import numpy as np
import time
start = time.time()
print("\n(Map) multiplying 32 million elements by 2")
dbls=np.arange(32000000)*2
print("(Reduce) sum: %d" % sum(dbls))
end = time.time()
print("Total MapReduce time: %f" % (end-start))
