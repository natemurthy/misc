# Given two strings, check if they’re anagrams or not. Two strings are 
# anagrams if they are written using the same exact letters, ignoring 
# space, punctuation and capitalization. Each letter should have the 
# same count in both strings. For example, ‘Eleven plus two’ and 
# ‘Twelve plus one’ are meaningful anagrams of each other.

import collections
import string

# quick and dirty O(n log n) solution
def is_anagram(str1, str2):
    return sorted(get_letters(str1))==sorted(get_letters(str2))
 
def get_letters(text):
    return [char.lower() for char in text if char in string.letters]


# more efficient O(n) solution
def is_anagram_2(str1, str2):
    str1, str2 = get_letters(str1), get_letters(str2)
    if len(str1)!=len(str2):
        return False
    counts=collections.defaultdict(int)
    for letter in str1:
        counts[letter]+=1
    for letter in str2:
        counts[letter]-=1
        if counts[letter]<0:
            return False
    return True
