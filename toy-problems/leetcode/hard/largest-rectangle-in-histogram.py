"""
https://leetcode.com/problems/largest-rectangle-in-histogram/

Input: [2,1,5,6,2,3]
Output: 10
"""

def solution(hist):
    widths = len(hist)
    heights = hist
    rectangles = []
    for h in heights:
        for w in widths:


