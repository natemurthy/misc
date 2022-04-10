# /*

# Given an array of integers, determine whether the array only increases or only decreases.

# Examples:

# [1, 2, 3] --> True
# [3, 2, 1] --> True
# [1, 2, 4, 4, 5] --> True
# [1, 1, 1] --> True

# */

'''
Here is a more elegant solution from g4g:

https://www.geeksforgeeks.org/python-program-to-check-if-given-array-is-monotonic/
'''

def is_monotonic(arr): 
    end = len(arr)-1
    return (all(arr[i] <= arr[i + 1] for i in range(end)) or
            all(arr[i] >= arr[i + 1] for i in range(end))) 

print(is_monotonic([1,2,1]))
print(is_monotonic([1, 2, 4, 4, 5]))
print(is_monotonic([1,1,1]))
print(is_monotonic([0, 3, 1,1, 0, 0, -1, -2]))

