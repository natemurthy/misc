#!/bin/env python

def test(expected, actual):
    if expected == actual:
        print("Pass")
    else:
        print("Fail (expected '{}', actual '{}')".format(expected, actual))

"""
Revenue Milestones
https://www.facebookrecruiting.com/portal/coding_practice_question/?problem_id=192049171861831
"""

def getMilestoneDays(revenues, milestones):
    
    days = []
    for m in milestones:
        total_revenue = 0
        for ix, r in enumerate(revenues):
            total_revenue += r
            if total_revenue >= m:
                days.append(ix+1)
                break
    return days

revenues_1 = [100, 200, 300, 400, 500]
milestones_1 = [300, 800, 1000, 1400]
expected_1 = [2, 4, 4, 5]
output_1 = getMilestoneDays(revenues_1, milestones_1)
test(expected_1, output_1)

revenues_2 = [700, 800, 600, 400, 600, 700]
milestones_2 = [3100, 2200, 800, 2100, 1000] 
expected_2 = [5, 4, 2, 3, 2]
output_2 = getMilestoneDays(revenues_2, milestones_2)
test(expected_2, output_2)

