"""
 input: array of integers
output: count of non-zero integers
        move all zeros to tail of array
"""


def move_zeros_to_tail_and_count_nonzeros(arr):
    j = 0; end = len(arr)-1; k = end
    for i,v in enumerate(arr):
        #print i, arr
        if i <= k and v == 0:
            while arr[k] == 0:
                j += 1
                k = end-j
                if k < 1:
                    break
            #print '    ', i, j, k, arr[k], arr
            if i <= k:
                temp = arr[k]
                arr[k] = v
                arr[i] = temp
                j += 1
                k = end-j
        else:
            continue
    return k+1


arr = [1, 2, 3, -4, 0, 0, 2, 4, 0]
print move_zeros_to_tail_and_count_nonzeros(arr)  == 6
print arr == [1, 2, 3, -4, 4, 2, 0, 0, 0]

arr = [1]
print move_zeros_to_tail_and_count_nonzeros(arr)  == 1
print arr == arr

arr = [0,0,0]
print move_zeros_to_tail_and_count_nonzeros(arr)  == 0
print arr == [0,0,0]

arr = [1,2,3,0,0]
print move_zeros_to_tail_and_count_nonzeros(arr)  == 3
print arr == [1,2,3,0,0]

arr = [0,0,1,2,3]
print move_zeros_to_tail_and_count_nonzeros(arr)  == 3
print arr == [3,2,1,0,0]

arr = [1,0,1,0,1,0]
print move_zeros_to_tail_and_count_nonzeros(arr)  == 3
print arr == [1,1,1,0,0,0]

arr = [1,0,1,0,1]
print move_zeros_to_tail_and_count_nonzeros(arr)  == 3
print arr == [1,1,1,0,0]

arr = [0,1,0,1,0,1]
print move_zeros_to_tail_and_count_nonzeros(arr)  == 3
print arr == [1,1,1,0,0,0]

arr = [0,1,0,1,0,1,0]
print move_zeros_to_tail_and_count_nonzeros(arr)  == 3
print arr == [1,1,1,0,0,0,0]
