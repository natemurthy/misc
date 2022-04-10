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

def min_meeting_rooms(arr):
    starts, ends = [], []
    for interval in arr:
        starts.append(interval[0])
        ends.append(interval[1])

    starts.sort()
    ends.sort()

    s, e = 0, 0
    min_rooms, cnt_rooms = 0, 0
    while s < len(starts):
        if starts[s] < ends[e]:
            cnt_rooms += 1
            min_rooms = max(min_rooms, cnt_rooms)
            s += 1
        else:
            cnt_rooms -= 1
            e += 1

    return min_rooms

arr = [(10,10.5), (10, 11), (13,14), (10.25, 10.5), (7, 8), (10, 11), (18, 19)]
print min_meeting_rooms(arr)

arr = [(1,2), (0,3)]
print min_meeting_rooms(arr)
