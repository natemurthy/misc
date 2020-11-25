"""
https://leetcode.com/problems/jump-game
"""

# my solution
def can_jump(arr):
    i = 0
    while i < len(arr):
        jump = arr[i]
        i += jump
        if i == len(arr)-1:
            return True
        elif jump == 0:
            return False
    return False

print can_jump([2,3,1,1,4])
print can_jump([3,2,1,0,4])
