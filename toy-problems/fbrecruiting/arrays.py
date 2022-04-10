#!/bin/env python

def test(expected, actual):
    if expected == actual:
        print("Pass")
    else:
        print("Fail (expected '{}', actual '{}')".format(expected, actual))



"""
Reverse to Make Equal
https://www.facebookrecruiting.com/portal/coding_practice_question/?problem_id=2869293499822992
"""
def are_they_equal(array_a, array_b):
  if len(array_a) != len(array_b):
      return False
  n = len(array_a)
  for i in range(n):
      for j in range(i+1, n):
          #print i, j, array_a[i:j+1], array_b[i:j+1][::-1]
          if array_a[i:j+1] == array_b[i:j+1][::-1]:
              return True
      
  return False

A = [1, 2, 3, 4]
B = [1, 4, 3, 2]
test(True, are_they_equal(A,B))

a_2 = [1, 2, 3, 4]
b_2 = [1, 2, 3, 5]  
test(False, are_they_equal(a_2, b_2))

"""
Passing Yearbooks
https://www.facebookrecruiting.com/portal/coding_practice_question/?problem_id=146466059993201
"""

def findSignatureCounts(arr):
    n = len(arr)
    counts = [1]*n
    for i in range(n):
        k = i
        while arr[k] != i+1:
            counts[i] += 1
            k = arr[k]-1
    return counts

arr_1 = [2, 1]
expected_1 = [2, 2]
output_1 = findSignatureCounts(arr_1)
test(expected_1, output_1)

arr_2 = [1, 2]
expected_2 = [1, 1]
output_2 = findSignatureCounts(arr_2)
test(expected_2, output_2)

arr_3 = [4,3,2,5,1]
expected_3 = [3,2,2,3,3]
output_3 = findSignatureCounts(arr_3)
test(expected_3, output_3)



"""
Contiguous Subarrays
https://www.facebookrecruiting.com/portal/coding_practice_question/?problem_id=226517205173943
"""

def count_subarrays(arr):
    n = len(arr)
    result = [1] * n
    for i, x in enumerate(arr):
        for di in [1, -1]:
            step = 1
            while 0 <= i+ di*step < n and  arr[i+ di*step] < x:
                result[i] += 1
                step += 1
    return result

test_1 = [3, 4, 1, 6, 2]
expected_1 = [1, 3, 1, 5, 1]
output_1 = count_subarrays(test_1)
test(expected_1, output_1)

test_2 = [2, 4, 7, 1, 5, 3]
expected_2 = [1, 2, 6, 1, 3, 1]
output_2 = count_subarrays(test_2)
test(expected_2, output_2)

