"""
https://www.geeksforgeeks.org/move-zeroes-end-array/

Function which pushes all zeros to end of an array and returns count of all
non zero values

Similar to coding problem asked during 2016-11-15 interview at Facebook
"""

def pushZerosToEnd(arr): 
    n = len(arr)
    count = 0
    k = 0
    
    for i in range(n): 
        if arr[i] != 0: 
            arr[k] = arr[i] 
            k += 1

    count = k
     
    while k < n: 
        arr[k] = 0
        k += 1

    return count

"""
Way more elegant solution
https://github.com/ChenglongChen/LeetCode-3/blob/master/Python/move-zeroes.py
"""
def swap(arr, i, j):
    arr[i], arr[j] = arr[j], arr[i]

def move_zeros(arr):
    k = 0
    n = len(arr)
    for i in range(n):
        if arr[i]:
            swap(arr, i, k)
            k += 1
    return k

# Driver code 
arr = [1, 9, 8, 4, 0, 0, 2, 7, 0, 6, 0, 9] 
print pushZerosToEnd(arr) 
print(arr) 

print ""
# Driver code 
arr = [1, 9, 8, 4, 0, 0, 2, 7, 0, 6, 0, 9] 
print move_zeros(arr) 
print(arr) 


