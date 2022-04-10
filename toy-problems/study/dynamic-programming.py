"""
Given an array of N integers, find the length of the longest subsequence
of a given sequence such that all elements of the subsequence are sorted
in strictly decreasing order.

https://www.geeksforgeeks.org/longest-decreasing-subsequence/
"""
input = [15, 27, 14, 38, 63, 55, 46, 65, 85]

def find_longest_decreasing(arr):
    n = len(arr)
    lds = [1]*n

    for i in range(1,n):
        for j in range(0, i):
            if arr[j] > arr[i] and lds[j]+1 > lds[i]:
                lds[i] = lds[j] + 1

    return max(lds)

print find_longest_decreasing(input)


"""
longest increasing subsequence (this doesn't quite work?)
"""
def find_longest_inreasing(arr):
    n = len(arr)
    lis = [1]*n

    for i in range(1,n):
        for j in range(0, i):
            if arr[j] < arr[i] and lis[j]+1 > lis[i]:
                lis[i] = lis[j] + 1

    print lis
    return max(lis)

print find_longest_inreasing(input)
