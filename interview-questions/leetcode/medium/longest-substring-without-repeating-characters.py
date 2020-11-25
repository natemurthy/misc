#!/bin/env python

"""
https://leetcode.com/problems/longest-substring-without-repeating-characters/
"""

# TODO does not work for 3rd case, clarification on repetition
def solution(seq):

    if seq == "":
        return 0

    seen = []
    substrings = {}

    sub = ""

    for c in seq:
        sub += c
        if c not in seen:
            seen.append(c)
        else:
            n = len(sub)-1
            if c in sub[:n] and n > 0:
                sub = sub[:n]
            substrings[sub] = len(sub)
            sub = ""

    return substrings


print solution("abcabcbb")
print solution("bbbbb")
print solution("pwwkew")
print solution("")
print solution("aabcdef")

