def is_monotonic(arr):
    n = len(arr)-1
    if n < 2:
        return True
    increasing, decreasing = True, True
    for i in range(n):
        if arr[i] > arr[i+1]:
            increasing = False
        elif arr[i] < arr[i+1]:
            decreasing = False
    return increasing or decreasing


print(is_monotonic([1,2,1]))
print(is_monotonic([1, 2, 4, 4, 5]))
print(is_monotonic([1,1,1]))
print(is_monotonic([0, 3, 1,1, 0, 0, -1, -2]))
