"""
Given a set represented as string, write a recursive code to print all subsets of it.
The subsets can be printed in any order.

https://www.geeksforgeeks.org/recursive-program-to-generate-power-set/
"""

def power_set1(s, index=-1, curr=""):

    n = len(s)
    if index == n:
        return

    print curr

    i = index+1
    while i < n:

        curr += s[i]

        power_set1(s, i, curr)

        curr = curr[:-1]
        i += 1

    return

power_set1("abc")

print "---------------"

def power_set2(s, index=0, curr=""):
    n = len(s)
    
    if index == n:
        print curr
        return
    
    power_set2(s, index+1, curr+s[index])
    power_set2(s, index+1, curr)


power_set2("abc")
