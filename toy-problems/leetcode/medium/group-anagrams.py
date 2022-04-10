"""
https://leetcode.com/problems/group-anagrams/

Given an array of strings, group all anagrams together in nested list

Examples

Input: strs = ["eat","tea","tan","ate","nat","bat"]
Output: [["bat"],["nat","tan"],["ate","eat","tea"]]


Input: strs = [""]
Output: [[""]]

Input: strs = ["a"]
Output: [["a"]]

Notes:
Easiest way to determine if two words are anagrams is by sorting all of their
characters
"""

import collections

def group_anagrams(strs):
    result = []
    anagram_map = collections.defaultdict(list)
    for s in strs:
        sorted_str = "".join(sorted(s)) # this is important part
        anagram_map[sorted_str].append(s)

    for s in anagram_map.values():
        s.sort() # don't really need this, but makes things cleaner
        result.append(s)
    return result

print group_anagrams(["eat","tea","tan","ate","nat","bat"])


