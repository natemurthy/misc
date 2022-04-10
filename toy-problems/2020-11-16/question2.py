"""
given a bench of some length N (i.e. of fixed seats N), find the
placement of people on the bench such that the distance between all
the people is maximized if one new person?

given a bench of some length N (i.e. number of fixed seats is N), find
which seat is the best seat to place another person N+1 to the bench
such that the distance between them and the next person is maximized?

e.g. bench with 10 seats and 3 people sitting on it

bench = [1,1,1,0,0,0,0,0,0,0]
then i = 9 is the best seat if another person is added

"""

def max_dist(bench):
    n = len(bench)
    open_seating = []
    i = 0
    while i < n:
        if bench[i]:
            i += 1
            continue
        else:
            l = i
            while not bench[i] and i < n-1:
                i += 1
            r = i
            open_seating.append([l, r])
            i += 1

    #print open_seating

    num_most_seats = float("-inf")
    most_seats = []

    for s in open_seating:
        if s[1]-s[0] > num_most_seats:
            num_most_seats = s[1]-s[0]
            most_seats = s

    #print most_seats

    l, r = most_seats[0], most_seats[1]

    best_seat = l + (r-l)/2

    if r == n-1 and not bench[r]:
        best_seat = r
    elif l == 0 and not bench[l]:
        best_seat = l
    
    return best_seat


# n = 10
bench = [0,0,0,0,0,0,1,1,0,1]
print max_dist(bench) == 0

bench = [1,1,1,0,0,0,0,0,0,0]
print max_dist(bench) == 9

bench = [0,0,1,0,1,0,0,0,1,0]
print max_dist(bench) == 6
 



"""
my initial reasoning which was not helpful:

distance between people will be the number of seats between them

bench = _ _ x _ x _ _ _ x _  

bench = [0,0,1,0,1,0,0,0,1,0]
dist  = {
    2: [2, 1],
    4: [1, 2],
    7: [2, 1]
}

l=0, r=9
bench[0] == 0, l=1   | bench[9] == 0, r=8
bench[1] == 0, l=2   | bench[8] == 0, r=7
bench[2] == 1, l=2   | bench[7] == 1, r=7 =>  max_dist(2, 9-7)  = 2 => l=3, r =6
bench[3] == 0, l=4   | bench[6] == 0, r=5
bench[4] == 1, 
     

bench = x x x _ _ _ _ _ _ _

bench = [1,1,1,0,0,0,0,0,0,0]
dist  = {
    0: [0, 0],
    1: [0, 0],
    2: [0, 7]
}

"""


