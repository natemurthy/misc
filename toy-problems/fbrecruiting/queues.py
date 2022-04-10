#!/bin/env python

def test(expected, actual):
    if expected == actual:
        print("Pass")
    else:
        print("Fail (expected '{}', actual '{}')".format(expected, actual))

"""
Queue Removals

https://www.facebookrecruiting.com/portal/coding_practice_question/?problem_id=229890198389794
"""

def findPositions(arr, x):
    return []

n_1 = 6
x_1 = 5
arr_1 = [1, 2, 2, 3, 4, 5]
expected_1 = [5, 6, 4, 1, 2]
output_1 = findPositions(arr_1, x_1)
test(expected_1, output_1)

n_2 = 13
x_2 = 4
arr_2 = [2, 4, 2, 4, 3, 1, 2, 2, 3, 4, 3, 4, 4]
expected_2 = [2, 5, 10, 13]
output_2 = findPositions(arr_2, x_2)
test(expected_2, output_2)
