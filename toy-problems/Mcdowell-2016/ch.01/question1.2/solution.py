#!/bin/env python
"""
Similar to is_anagram solution from:
    2014-05-08/question1.py


Steps:

1. if string lengths are different then obviously not a permutation
2. build a dictionary of each letter occurrence from first string
3. remove each letter occurrence from the dict and sum all its values
4. if the sum of all the values does not equal 0 then the strings are not permutations
   of each other
5. otherwise they are permutations
"""

import collections

def is_permutation(a,b):

    # step 1
    if len(a) != len(b):
        return False

    # initializes all values to zero integer, otherwise need to do extra step of
    # checking whether key exists in dict before incrementing
    counts = collections.defaultdict(int)

    # step 2
    for letter in a:
        counts[letter] += 1

    # step 3
    for letter in b:
        counts[letter] -= 1

    # step 4
    for c in counts.values():
        if c != 0 :
            return False

    # step 5
    return True


print is_permutation("eleven plus two", "twelve plus one")
print is_permutation("one","two")

