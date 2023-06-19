"""
calculate mean and then calculate variance

note: 
https://en.wikipedia.org/wiki/Variance#:~:text=n%20%E2%88%92%201%20eliminates%20bias
"""

from typing import List

def mean(arr: List[float]) -> float:
    return sum(arr)/len(arr)

def var(arr: List[float]) -> float:
    mu = mean(arr)
    res = 0.0
    for x in arr:
        res += (x - mu)**2
    return res / (len(arr)-1) # see note above about using n-1 to avoid bias

def biased_var(arr: List[float]) -> float:
    mu = mean(arr)
    res = 0.0
    for x in arr:
        res += (x - mu)**2
    return res / len(arr)


"""
Compare var(xs) with biased_var(xs)
"""

xs = [1.0,2.0,3.0]
print("mean      :", mean(xs))
print("var       :", var(xs))         # unbiased value: 1.0
print("biased_var:", biased_var(xs))  # showing bias  : 0.6666666666666666

#https://colab.research.google.com/drive/1gZga2zQEG-CHqU9srZ1Tzo0k83YSfUYA
#import numpy as np
#print("np.var    :", np.var(xs))      # same as biased_var
