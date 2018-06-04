import numpy as np

def is_pos_def(x):
    return np.all(np.linalg.eigvals(x) > 0)

a = np.random.rand(1000, 1000)
print is_pos_def(a)
