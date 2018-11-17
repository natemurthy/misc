"""
https://www.geeksforgeeks.org/move-zeroes-end-array/

Function which pushes all zeros to end of an array.
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
		
# Driver code 
arr = [1, 9, 8, 4, 0, 0, 2, 7, 0, 6, 0, 9] 
print pushZerosToEnd(arr) 
print("Array after pushing all zeros to end of array:") 
print(arr) 


