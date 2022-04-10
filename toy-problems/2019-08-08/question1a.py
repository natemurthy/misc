# /*

# Given an array of integers, determine whether the array only increases or only decreases.

# Examples:

# [1, 2, 3] --> True
# [3, 2, 1] --> True
# [1, 2, 4, 4, 5] --> True
# [1, 1, 1] --> True


# */

'''
[3, 3, 1, 1,1, 0, 0, -1, -2] --> True
[3, 3, ... , 3, 1, 1, 1]
'''

def is_monotonic(arr):
    _is_monotonic = True
    cursor = 0
    end = len(arr)-1

    if len(arr) < 1:
        return _is_monotonic

    for i in range(cursor, end):
        if arr[i] == arr[i+1]:
            cursor += 1
        else:
            break
            
    if cursor == end:
        return _is_monotonic
    
    is_decreasing = arr[cursor] > arr[cursor+1]

    cursor += 1
    
    if is_decreasing:
        for i in range(cursor, end):
            if arr[i] < arr[i+1]:
                _is_monotonic = False
                break
    else:
        for i in range(cursor, end):
            if arr[i] > arr[i+1]:
                _is_monotonic = False
                break
    
    return _is_monotonic

print(is_monotonic([1,2,1]))
print(is_monotonic([1, 2, 4, 4, 5]))
print(is_monotonic([1,1,1]))
print(is_monotonic([0, 3, 1,1, 0, 0, -1, -2]))

