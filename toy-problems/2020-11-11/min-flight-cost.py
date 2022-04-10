"""

Plan a round trip between two cities with minimum flight cost.

From departure city A to destination city B, the direct flight fee is stored in array D[].
From destination city B to departure city A, the direct flight fee is stored in array R[].

             0   1  2  3  4  <-- day
Departure: [10, 8, 9, 11, 7] <-- price A->B
Return:    [ 8, 8, 10, 7, 9] <-- price B->A

Constraint: you cannot travel back on a previous day. 

The minimum cost will be D[1] + R[3] = 15
"""


def minimize_cost(D, R):    
    n = len(D)
    
    r_cost = float("inf")
    min_r = []
    i = n-1
    while i >= 0:
        tmp = min(r_cost, R[i])
        min_r.insert(0, tmp)
        r_cost = tmp
        i -= 1

    print min_r
        
    total_cost = float("inf")
    for j in range(n):
        if D[j] + min_r[j] < total_cost:
            total_cost = D[j] + min_r[j]
            
    return total_cost


D = [10, 8, 9, 11, 7]
R = [ 8, 8, 10, 7, 9]
print minimize_cost(D, R) == 15
