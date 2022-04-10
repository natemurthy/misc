
def search(arr, x):
    i = 0
    while i < len(arr):
        if arr[i] == x:
            return i
        i += abs(arr[i]-x)
    return 0

arr = [1,2,3,4,3,2,1,2,3,4,3,4,5]
print search(arr,4)


