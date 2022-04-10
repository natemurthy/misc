#!/bin/env python

def test(expected, actual):
    if expected == actual:
        print("Pass")
    else:
        print("Fail (expected '{}', actual '{}')".format(expected, actual))


"""
Largest Triple Products
https://www.facebookrecruiting.com/portal/coding_practice_question/?problem_id=510655302929581
"""
import heapq

def findMaxProduct(arr):
    # Write your code here
    result = [-1,-1]
    n = len(arr)
    for i in range(2,n):
        subarr = arr[0:i+1]
        heapq._heapify_max(subarr)
        p = 1
        for _ in range(3):
            p *= heapq.heappop(subarr)
            heapq._heapify_max(subarr)
        result.append(p)
    return result

input_1 = [1, 2, 3, 4, 5]
expected_1 = [-1, -1, 6, 24, 60]
test(expected_1, findMaxProduct(input_1))

input_2 = [2, 1, 2, 1, 2]
expected_2 = [-1, -1, 4, 4, 8]
test(expected_2, findMaxProduct(input_2))

"""
Magical Candy Bags
https://www.facebookrecruiting.com/portal/coding_practice_question/?problem_id=513590792640579
"""

def maxCandies(arr, k):
    n = len(arr)
    result = 0
    while k > 0:
        heapq._heapify_max(arr)
        x = heapq.heappop(arr)
        result += x
        arr.append(x//2)
        k -= 1
    return result

n_1, k_1 = 5, 3
arr_1 = [2, 1, 7, 4, 2]
expected_1 = 14
output_1 = maxCandies(arr_1, k_1)
test(expected_1, output_1)

n_2, k_2 = 9, 3
arr_2 = [19, 78, 76, 72, 48, 8, 24, 74, 29]
expected_2 = 228
output_2 = maxCandies(arr_2, k_2)
test(expected_2, output_2)

