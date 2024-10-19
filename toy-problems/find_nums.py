#!/bin/env python3


def missing_nums1(arr):
    ref = range(0,len(arr)+1)

    #print(arr)
    #print(ref)
    for x in ref:
        if x not in arr:
            print(x)
            return x


def missing_nums2(arr):
    ref = range(0,len(arr)+1)
    res = sum(ref) - sum(arr)
    return res


def missing_nums3(arr):
    n = len(arr)
    ref = (n*(n+1))/2
    res = ref - sum(arr)
    return res


num_inputs = [
        [3,0,1],
        [0,1],
        [9,6,4,2,3,5,7,0,1],
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99]
]


for nums in num_inputs:
    print(missing_nums1(nums) == missing_nums2(nums))
    print(missing_nums1(nums) == missing_nums3(nums))

