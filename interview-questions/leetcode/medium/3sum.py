"""
https://leetcode.com/problems/3sum/

O(n^2) solution inspired by:
https://www.geeksforgeeks.org/count-triplets-with-sum-smaller-that-a-given-value/
"""

def triplet_sum(arr):
    n = len(arr)
    arr.sort()
    res = []
    for i in range(0, n-2):
        j = i+1
        k = n-1
        while j < k:
            if arr[i]+arr[j]+arr[k] == 0:
                res.append([arr[i],arr[j],arr[k]])
                k -= 1
            else:
                j += 1
    return res

actual = triplet_sum([-1, 0, 1, 2, -1, -4])
for a in actual:
    print(a)

expected = [[-1, -1, 2], [-1, 0, 1]]
print(actual == expected)
