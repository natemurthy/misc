"""
https://leetcode.com/problems/container-with-most-water/
"""

def max_area(arr):
    l = 0
    r = len(arr)-1
    A = 0
    while l < r:
        A = max(A, (r-l)*min(arr[l], arr[r]))
        if arr[l] < arr[r]:
            l += 1
        else:
            r -= 1
    return A


arr = [1,8,6,2,5,4,8,3,7]
print(max_area(arr)==49)
