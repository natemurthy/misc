#!/bin/env python

"""
In general, greedy algorithms have the five components:

    1. a candidate set, from which a solution is created
    2. a selection function, which chooses the best candidate to be added to the solution
    3. a feasability function, that is used to determine if a candidate can be used to
       contribute to a solution
    4. an objective function, which assigns a value to a solution or partial solution
    5. a solution function, which will indicate when we have discovered a complete solution
"""
def test(expected, actual):
    if expected == actual:
        print("Pass")
    else:
        print("Fail (expected '{}', actual '{}')".format(expected, actual))

"""
Slow Sums
https://www.facebookrecruiting.com/portal/coding_practice_question/?problem_id=836241573518034

For this problem, we will iterate over each element in the candidate set and sum pairs of
elements by selecting the largest two elements in the array. 
"""


def getTotalTime(arr):
    if len(arr) <= 2:
        return sum(arr)
    else:
        arr.sort()
        penalty = arr.pop() + arr.pop()
        arr.append(penalty)
        penalty += getTotalTime(arr)
        return penalty

arr_1 = [4, 2, 1, 3]
expected_1 = 26
output_1 = getTotalTime(arr_1)
test(expected_1, output_1)

arr_2 = [2, 3, 9, 8, 4]
expected_2 = 88
output_2 = getTotalTime(arr_2)
test(expected_2, output_2)
