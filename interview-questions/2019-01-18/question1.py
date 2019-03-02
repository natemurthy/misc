"""
Custom Sort Order
Given a list of strings and a list of characters that specifies a custom sort ordering,
return true if the strings are sorted in the correct order otherwise return false

Example:
Strings: ["cb", "ca", "bc", "ba"] Order: ['c', 'b', 'a'] -> True
Strings: ["bc", "ab", "ac", "ca"] Order: ['c', 'b', 'a'] -> False
Strings ["catt", "cat", "bat"] Order ['c', 'b', 'a', 't'] -> False
"""

def check_ordering(arr, order):
    in_order = False
    
    n = len(arr)-1
    order_dict = {}
    for v, k in enumerate(order):
        order_dict[k] = v
        
    for i in range(n):
        s1 = arr[i]
        s2 = arr[i+1]
        
        len_s1 = len(s1)
        len_s2 = len(s2)
        
        min_len = min(len_s1, len_s2)
        
        if s1[0:min_len] == s2[0:min_len] and len_s1 > len_s2:
            return False
        
        for j in range(min_len):
            c1 = s1[j]
            c2 = s2[j]
            
            if order_dict[c1] <= order_dict[c2]:
                in_order = True
            else:
                in_order = False
                break
        
    return in_order


def sort_with_ordering(arr, order):
    order_dict = {}
    for v, k in enumerate(order):
        order_dict[k] = v

    def compare(x, y):
        len_x = len(x)
        len_y = len(y)
        min_len = min(len_x, len_y)
        if x[0:min_len] == y[0:min_len] and len_x > len_y:
            return 1
        for j in range(min_len):
            if order_dict[x[j]] < order_dict[y[j]]:
                return -1
            elif order_dict[x[j]] == order_dict[y[j]]:
                return 0
            else:
                return 1

    return sorted(arr, cmp=compare)
    
print(check_ordering(["cb", "ca", "bc", "ba"], ['c', 'b', 'a']))
print(check_ordering(["bc", "ab", "ac", "ca"], ['c', 'b', 'a']))
print(check_ordering(["catt", "cat", "bat"],   ['c', 'b', 'a', 't']))

print(sort_with_ordering(["cb", "ca", "bc", "ba"], ['c', 'b', 'a']))
print(sort_with_ordering(["bc", "ab", "ac", "ca"], ['c', 'b', 'a']))
print(sort_with_ordering(["catt", "cat", "bat"],   ['c', 'b', 'a', 't']))
