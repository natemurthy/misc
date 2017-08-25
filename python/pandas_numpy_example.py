# See https://stackoverflow.com/questions/32752292/pandas-how-to-create-a-data-frame-of-random-integers
# And https://stackoverflow.com/questions/12137277/how-can-i-make-a-python-numpy-arange-of-datetime

import numpy as np
import pandas as pd
import datetime as dt

N = 10
df = pd.DataFrame(np.random.randn(N, 4), columns=list('ABCD'))
start = dt.datetime(2017, 1, 1)
arr = np.array([start + dt.timedelta(hours=i) for i in xrange(N)])
df = df.set_index(arr)
