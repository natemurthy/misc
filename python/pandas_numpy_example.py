import numpy as np
import pandas as pd
import datetime as dt

# 
# See https://stackoverflow.com/questions/32752292/pandas-how-to-create-a-data-frame-of-random-integers
# And https://stackoverflow.com/questions/12137277/how-can-i-make-a-python-numpy-arange-of-datetime

N = 10
df = pd.DataFrame(np.random.randn(N, 4), columns=list('ABCD'))
start = datetime.datetime(2017, 1, 1)
arr = np.array([start + datetime.timedelta(hours=i) for i in xrange(N)])
