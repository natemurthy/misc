import pandas as pd
import time
start = time.time()
print("\n(Map) multiplying 32 million elements by 2")
dbls=pd.Series(range(32000000))*2
print("(Reduce) sum: %d" % dbls.sum())
end = time.time()
print("Total MapReduce time: %f" % (end-start))
