"""
https://leetcode.com/problems/sum-of-subarray-minimums/
"""

def gen_subarray_mins(arr, s):
    sub_mins = []
    i = 0
    for i in xrange(len(arr)):
        sub = arr[i:i+s]
        if len(sub) == s:
            print(sub)
            sub_mins.append(min(sub))
        i = i+s
    return sub_mins

def sum_of_mins(arr):
    acc = 0
    for i in xrange(len(arr)):
        acc += sum(gen_subarray_mins(arr,i+1))
    return acc

# test
arr = [3,1,2,4]
print(sum_of_mins(arr) == 17)
