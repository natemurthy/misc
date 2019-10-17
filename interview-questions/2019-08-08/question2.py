# /*
 
# Given an arbitrary list of meeting times, determine the minimum number of meeting rooms that are needed.

# Example: 
# 10am - 10:30am
#  10am - 11am
#  11am - 12pm
#  1pm - 2pm

# min #meeting rooms returns 2
# */

'''
arr = [(10,10.5), (10, 11), (13,14), (10.25, 10.5), (7, 8), (10, 11), (18, 19)]

sorted(arr) == [(7, 8), (10, 11), (10, 11), 10,10.5), (13,14), (18, 19)]
'''

# TODO
def how_many_rooms(arr):
    if len(arr) < 1:
        return 0
    
    count = 1
    
    overlaps = []
    
    index = 0
    
    for i, _ in enumerate(arr[:len(arr)]):
        if arr[i][1] > arr[i+1][0]:
            count += 1
            overlap.append((arr[i][0], arr[i+1][1]))
            index = i
            
    for i, _ in overlaps:
        if arr[index][1] > overlaps[i][0]:
            count += 1
          
    return count

