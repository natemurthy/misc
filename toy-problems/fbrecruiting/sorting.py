#!/bin/env python

def test(expected, actual):
    if expected == actual:
        print("Pass")
    else:
        print("Fail (expected '{}', actual '{}')".format(expected, actual))

"""
Balanced Split
https://www.facebookrecruiting.com/portal/coding_practice_question/?problem_id=226994905008716
"""

def balancedSplitExists(arr):
    arr.sort()
    n = len(arr)
    for i in range(1,n):
        if sum(arr[0:i]) == sum(arr[i:]) and arr[i-1] < arr[i]:
            return True
    return False


arr_1 = [2, 1, 2, 5]
expected_1 = True
output_1 = balancedSplitExists(arr_1)
test(expected_1, output_1)

arr_2 = [3, 6, 3, 4, 4]
expected_2 = False
output_2 = balancedSplitExists(arr_2)
test(expected_2, output_2)
