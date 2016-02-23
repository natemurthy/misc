# Merge two sorted arrays

l = [1,2,6,8,10]
r = [2,5,6,9]

out = [1,2,2,5,6,8,9,10]

def merge_sorted_lists(left, right):
    def insert_in_order(value,arr):
        pos = 0
        for v in arr:
            if value <= v:
                return arr[:pos]+[value]+arr[pos:]
            pos += 1
    for v in right:
        left = insert_in_order(v,left)
    return left

merge_sorted_lists(l,r)==out
