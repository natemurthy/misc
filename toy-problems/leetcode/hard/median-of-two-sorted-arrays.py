#!/bin/env python
"""
https://leetcode.com/problems/median-of-two-sorted-arrays/

naive approach would be two merge the two arrays, but that would cost O(n1+n2)
and we want O(log(n1+n2)) so maybe we should consider a binary search algorithm
 involving trees?

Considerations:
https://medium.com/@hazemu/finding-the-median-of-2-sorted-arrays-in-logarithmic-time-1d3f2ecbeb46

"I do not think a problem like this is appropriate for typical 1-hour interview sessions.
Solving such a problem requires a great deal of reflection and an even greater deal of
validation."

"""


def solution(arr1, arr2):
    n1 = len(arr1)
    n2 = len(arr2)
    # consider using bitshift operator if n1 and n2 are near overflow limit:
    # https://ai.googleblog.com/2006/06/extra-extra-read-all-about-it-nearly.html

    if n1 == 0 and n2 > 0:
        mid = n2/2
        if is_odd(n2):
            return arr2[mid]
        else:
            return (arr2[mid-1]+arr2[mid])/2.0

    if n1 > 0 and n2 == 0:
        mid = n1/2
        if is_odd(n1):
            return arr1[mid]
        else:
            return (arr2[mid-1]+arr2[mid])/2.0

    if n1 > 0 and n2 > 0:
        # this is the hard part
        pass

    return 0

def is_odd(n):
    return n % 2 == 1


a = [1,2,3,4]
b = []

print(solution(b,a))


def binary_search(arr, key):
    low = 0
    high = len(arr)-1
    
    while low <= high:
        mid = (low+high)/2
        midval = arr[mid]
        if midval < key:
            low = mid+1
        elif midval > key:
            high = mid-1
        else:
            return mid
    return -1

