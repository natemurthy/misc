# the one interview question i bombed

import time

def divisor1(N, numbers):
    result = 0
    for i in range(1,N+1):
        divisible = False
        for j in numbers:
            if i % j == 0:
                divisible = True
        if divisible:
            result += 1
    return result

t1 = time.time()
d1 = divisor1(1000000, [2,3,4,6])
t2 = time.time()
print t2-t1


def divisor2(N, numbers):
    if len(numbers) == 1:
        return N/numbers[0]
    else:
        result = 0
        for n in numbers:
            result += N/n
        for i in range(len(numbers)-1):
            for j in range(i+1, len(numbers)):
		if numbers[j] % numbers[i] == 0:
		    result -= N/numbers[j]
        return result

t1 = time.time()
d2 = divisor2(1000000, [2,3,4,6])
t2 = time.time()
print t2-t1

print "pass:", d1==d2
