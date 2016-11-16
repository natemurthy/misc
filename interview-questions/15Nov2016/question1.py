"""
 input: array of integers
output: count of non-zero integers
        move all zeros to tail of array
"""

arr = [1,2,3,-4,0,0,2,4,0]

def move_zeros_to_tail_and_count_nonzeros(arr):
    j = 0; k = len(arr)-1
    for i,v in enumerate(arr):
        if i < k and v == 0:
            try: 
                while arr[k] == 0:
                    j += 1
                    k = len(arr)-j-1
            except IndexError:
                return 0
            temp = arr[k]
            arr[k] = v
            arr[i] = temp
            j += 1
            k = len(arr)-j-1
        else:
            continue
    return k+1
         
