"""
flipping pancakes
input:  [4, 1, 5, 3, 2]
output: [1, 2, 3, 4, 5]
"""

def flip(arr, i):
    sub_arr = arr[0:i+1]
    return sub_arr[::-1] + arr[i+1:len(arr)]

def sort(arr):
    end = len(arr)-1
    for i in range(end):
        #print i, arr
        max_val = max(arr[0:len(arr)-i])
        for ii, v in enumerate(arr):
            if max_val == v:
                index = ii
                break
        tmp = flip(arr, index)
        #print '   ', index, tmp
        arr = flip(tmp, end-i)
        #print '   ', end-i, arr
    return arr


arr = [4, 1, 5, 3, 2]
print sort(arr) == [1, 2, 3, 4, 5]

arr = [2394, 12, 44, 980, 63, -4]
print sort(arr) == [-4, 12, 44, 63, 980, 2394]

arr = [5, 1, 1, 1, 1]
print sort(arr) == [1, 1, 1, 1, 5]

arr = [1, 1, 1, 1, 5]
print sort(arr) == [1, 1, 1, 1, 5]
