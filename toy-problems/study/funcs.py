def fib(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a+b
    return a

print [fib(x) for x in range(11)]


def factorial(n):
    a = n
    for i in range(1,n):
        a = a*(n-i)

    return a

print factorial(6)
