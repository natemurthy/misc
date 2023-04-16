"""
Check if x is prime

https://www.geeksforgeeks.org/python-program-to-check-whether-a-number-is-prime-or-not/

https://en.wikipedia.org/wiki/Primality_test
"""

def is_prime(x:int) -> bool:
    return is_prime_trial_division(x)
    #return is_prime_faster(x)

def is_prime_trial_division(x: int) -> bool:
    for i in range(2,x):
        if x % i == 0:
            #print("smallest divisor:", i)
            return False
    return True


def is_prime_faster(n: int) -> bool:
    """
    6k + 1 method
    """
    if n <= 3:
        return n > 1
    if n % 2 == 0 or n % 3 == 0:
        return False
    limit = int(n**0.5)
    for i in range(5, limit+1, 6):
        if n % i == 0 or n % (i+2) == 0:
            return False
    return True


import sys

prime_nums = [2,3,5,37,83]
composites = [4,121,221,8633]
large = [sys.maxsize]

def test_case(i):
    if is_prime(i):
        print("{} is prime".format(i))
    else:
        print("{} is composite".format(i))

for n in prime_nums + composites + large:
    test_case(n)

