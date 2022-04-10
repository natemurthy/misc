"""
https://leetcode.com/problems/4sum/
"""

def four_sum1(arr):
    n = len(arr)
    solns = []

    for i in range(0, n-3):
        for j in range(i+1, n-2):
            for k in range(i+2,n-1):
                for l in range(i+3,n):
                    if arr[i]+arr[j]+arr[k]+arr[l] == 0:
                        solns.append([arr[i],arr[j],arr[k],arr[l]])
    return solns

#actual = four_sum1([1, 0, -1, 0, -2, 2])


# Better solution that is O(n^3) and has fewer duplicates
# https://www.geeksforgeeks.org/find-four-numbers-with-sum-equal-to-given-sum/
def four_sum2(arr, target):
    n = len(arr)
    arr.sort()
    solns = []
    for i in range(0, n-3):
        for j in range(i+1, n-2):
            l = j+1
            r = n-1
            while l < r:
                if arr[i]+arr[j]+arr[l]+arr[r] == target:
                    solns.append([arr[i],arr[j],arr[l],arr[r]])
                    l += 1
                    r -= 1
                elif arr[i]+arr[j]+arr[l]+arr[r] < target:
                    l += 1
                else:
                    r -= 1
    return solns

actual = four_sum2([1, 4, 45, 6, 10, 12], 21)


# And an even better solution that is O(n^2 log n)
# https://www.geeksforgeeks.org/find-four-elements-that-sum-to-a-given-value-set-2/
def four_sum3(arr, target):
    pass

for a in actual:
    print(a)

