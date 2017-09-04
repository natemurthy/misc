import time
from numpy import poly1d

def dx(f, x):
    return abs(0-f(x))
 
def newtons_method(f, df, x0, e):
    delta = dx(f, x0)
    while delta > e:
        print 'Converging: delta=', delta
        x0 = x0 - f(x0)/df(x0)
        delta = dx(f, x0)
        time.sleep(0.5)
    print 'Root is at: ', x0
    print 'f(x) at root is: ', f(x0)

f = poly1d([6,-5,-4,3,0,0])
 
df = f.deriv(m=1)

newtons_method(f, df, 0.5, 1e-32)
