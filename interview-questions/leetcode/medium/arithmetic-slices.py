"""
https://leetcode.com/problems/arithmetic-slices/


"""
def sum_arithmetic(n):
    # sum of all ints 1 .. n
    return int((n/2.0)*(1+n))

def numberOfArithmeticSlices(arr):

    n = len(arr)-1

    all_diffs = []

    for i in range(n):
        diff = abs(arr[i]-arr[i+1])
        all_diffs.append(diff)

    unique_diffs = set(all_diffs)
    
    # using a dictionary for debugging purposes so that
    # we can look at the total count of all slices of the
    # same diff
    count_diffs = {}

    for i in unique_diffs:
        count = 0
        for j in all_diffs:
            if i == j:
                count += 1
        count_diffs[i] = count

    result = 0
    for k in count_diffs.values():
        if k == 2:
            result += 1
        elif k > 2:
            result += sum_arithmetic(k-1)

    return result


"""
Sample work:

A = [1, 3, 5, 7, 9]
1,3,5
3,5,7
5,7,9
1,3,5,7
2,5,7,9
1,3,5,7,9
len = 5, k = 6


A = [7, 7, 7, 7]
7,7,7
7,7,7
7,7,7,7
len =4, k = 3
A = [3, -1, -5, -9]
3,-1,-5
-1,-5,-9

A = [1, 2, 3, 4]

[1,2,3,4,5,6]
123
234
345
456
1234
2345
3456
12345
23456
123456
len = 6, k = 10

4+3+2+1

5/2 * 5 * 1

(n/2)(n+1) => 4/2*5
"""
