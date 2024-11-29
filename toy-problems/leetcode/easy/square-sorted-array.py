# https://leetcode.com/problems/squares-of-a-sorted-array/

"""
Example 1

Input: nums = [-4,-1,0,3,10]
Output: [0,1,9,16,100]
Explanation: After squaring, the array becomes [16,1,0,9,100].
After sorting, it becomes [0,1,9,16,100].


Example 2

Input: nums = [-7,-3,2,3,11]
Output: [4,9,9,49,121]
"""

from typing import List


def check(test_case: str, arr1: List[int], arr2: List[int]):
    if arr1 != arr2:
        print("{}: fail x".format(test_case))
        return
    print("{}: pass ✓".format(test_case))


def swap(arr: List[int], i: int, j: int):
    arr[i], arr[j] = arr[j], arr[i]


def reverse(arr: List[int], l, r):
    while l < r:
        arr[l], arr[r] = arr[r], arr[l]
        l += 1
        r -= 1


def sorted_squares(nums: List[int]):
    """
    Implements an in-place solution in O(n) time
    """
    n = len(nums)

    # Step 1: square all the nums
    for i in range(0, n):
        nums[i] = nums[i]**2
   
    # Step 2: find i where nums[i] < nums[i+1] and 
    # reverse nums[0] thru nums[i] then swap nums[i] and nums[i+1]
    # the swap can be done because we can rely on ascending sorted properties
    # of the array
    for i in range(0, n-1):
        if nums[i] < nums[i+1]:
            reverse(nums, 0, i) 
            if nums[i] > nums[i+1]:
                swap(nums, i, i+1)
            break

    return nums


nums = [-4,2,3]
expected = [4, 9, 16]
check("Example 0", sorted_squares(nums), expected)


nums = [-4,-1,0,3,10]
expected = [0,1,9,16,100]
check("Example 1", sorted_squares(nums), expected)


nums = [-7,-3,2,3,11]
expected = [4,9,9,49,121]
check("Example 2", sorted_squares(nums), expected)


# tests boundary condition for swap(nums, i, i+1)
nums = [-2,-1,0,3,10]
expected = [0,1,4,9,100]
check("Example 3", sorted_squares(nums), expected)


"""
Discussion:

O(n) solution to

https://leetcode.com/explore/interview/card/leetcodes-interview-crash-course-data-structures-and-algorithms/703/arraystrings/4689/

builds on

https://leetcode.com/explore/interview/card/leetcodes-interview-crash-course-data-structures-and-algorithms/703/arraystrings/4501/

and

https://leetcode.com/explore/interview/card/leetcodes-interview-crash-course-data-structures-and-algorithms/703/arraystrings/4592/
"""
