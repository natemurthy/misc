"""
Implement quicksort without memory constraint
"""
def quicksort(arr):
    less = []
    equal = []
    greater = []

    if len(arr) > 1:
        pivot = arr[-1]
        for x in arr:
            if x < pivot:
                less.append(x)
            if x == pivot:
                equal.append(x)
            if x > pivot:
                greater.append(x)

        return quicksort(less) + equal + quicksort(greater)
    else:
        return arr


"""
Implement in-place quicksort to limit memory to constant usage
"""
def swap(l, i, j):
    l[i], l[j] = l[j], l[i]

def partition(arr,low,high):
    i = low-1
    pivot = arr[high]

    for j in range(low , high):

    	if arr[j] <= pivot:
    	    #i = i+1
            swap(arr,i,j)
            i += 1

    swap(arr,i+1,high)
    return i+1

def qsort(arr,low,high):
    if low < high:
	p = partition(arr,low,high)
	qsort(arr, low, p-1)
	qsort(arr, p+1, high)

#arr = [12,4,-5,6,7,3,1,-15]
#qsort(arr,0,len(arr)-1)
#print arr


"""
Given an array of integers `arr`, find_pair searches for a pair of integers
from the input array such that the product of the two integers has the
closest absolute difference to some integer `x`. This implementation runs in
O(n) time by making use of the left-right approach.
"""
import sys

def find_pair(arr, x):
    l, r = 0, len(arr)-1
    final_l, final_r = l, r
    diff = sys.maxint
    
    while l < r:
        newdiff = abs(arr[l]*arr[r] - x)
        if newdiff < diff:
            final_l, final_r = l, r
            diff = newdiff
        if arr[l]*arr[r] > x:
            r -= 1
        else:
            l += 1
    return (arr[final_l], arr[final_r])
#arr = [2,3,5,9]
#print find_pair(arr, 47)
#print find_pair(arr, 8)


"""
Reverse an array of elements using the midpoint approach
"""
def reverse1(arr):
    n = len(arr)
    for i in range(n/2):
        arr[i], arr[n-1-i] = arr[n-1-i], arr[i]
    return arr


"""
Reverse an array of elements using the left-right approach
"""
def reverse2(arr):
    l, r = 0, len(arr)-1
    while l < r:
        arr[l], arr[r] = arr[r], arr[l]
        l += 1
        r -= 1

#arr = [1,2,4]
#reverse(arr)
#print arr


"""
Reverse the order of only alphabetical elements as they appear
in an array keepin non-alphabetical characters fixed. This runs
in O(n) time by way of the left-right approach.
"""
def reverse_alpha(s):
    arr = list(s)
    l = 0
    r = len(arr)-1

    while l < r:
        if not arr[l].isalpha():
            l += 1
        if not arr[r].isalpha():
            r -= 1

        arr[l], arr[r] = arr[r], arr[l]
        l += 1
        r -= 1

    return ''.join(arr)

#print reverse_alpha("a$bcd*")


"""
The is_palindrome checks if a given string is palindrome using
the left-right approach
"""
def is_palindrome(s):
    arr = list(s)
    l, r = 0, len(arr)-1
    while l < r:
        if arr[l] != arr[r]:
            return False
        l += 1
        r -= 1
    return True

#print is_palindrome("dad")
#print is_palindrome("god")


"""
Count triplets with sum smaller than a given value
Given an array of distinct integers and a sum value. Find count of triplets
with sum smaller than given sum value. Expected Time Complexity is O(n2).

https://www.geeksforgeeks.org/count-triplets-with-sum-smaller-that-a-given-value/

triplet_sum1 counts triplets in an array `arr` whose sum is
smaller than a given value `v` by way of searching all the
permutations of the given array
"""
from itertools import permutations

def triplet_sum1(arr, v):
    if len(arr) < 4 and sum(arr) < v:
        return 1

    triplets = []
    for p in permutations(arr):
        sub = set(p[0:3])
        if sum(sub) < v and sub not in triplets:
            triplets.append(sub)
    return len(triplets)


"""
triplet_sum2 counts triplets in an array `arr` whose sum is
smaller than a given value `v` using a brute force approach.
"""
def triplet_sum2(arr, v):
    count = 0
    n = len(arr)
    for i in range(0, n-2):
        for j in range(i+1, n-1):
            for k in range(j+1, n):
                if arr[i]+arr[j]+arr[k] < v:
                    count += 1
    return count

#print triplet_sum2([-2,0, 1, 3],     2)
#print triplet_sum2([5, 1, 3, 4, 7], 12)


"""
Given an array of integers `arr` and a gven number `v`, find the smallest subarray
with sum greater than the given value.

https://www.geeksforgeeks.org/minimum-length-subarray-sum-greater-given-value/
"""
def smallest_sub_sum(arr, v):
    n = len(arr)
    subarr = arr
    for i in range(n-1):
        for j in range(i+1, n):
            tmp = arr[i:j]
            if sum(tmp) > v and len(tmp) < len(subarr):
                subarr = tmp
    if sum(subarr) > v:
        return subarr
#print smallest_sub_sum([1, 4, 45, 6, 0, 19],                  51)
#print smallest_sub_sum([1, 10, 5, 2, 7],                       9)
#print smallest_sub_sum([1, 11, 100, 1, 0, 200, 3, 2, 1, 25], 280)
#print smallest_sub_sum([1,2,4],                                8)


"""
Check if characters of a given string can be rearranged to form a palindrome.

https://www.geeksforgeeks.org/check-characters-given-string-can-rearranged-form-palindrome/
"""
def check_palindrome(s):
    arr = list(s)
    for p in permutations(arr):
        if p == p[::-1]:
            return True
    return False

#print check_palindrome("dea")
#print check_palindrome("geeksogeeks")
