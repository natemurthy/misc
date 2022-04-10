#!/bin/env python

def test(expected, actual):
    if expected == actual:
        print("Pass")
    else:
        print("Fail (expected '{}', actual '{}')".format(expected, actual))

"""
Encrypted Words
https://www.facebookrecruiting.com/portal/coding_practice_question/?problem_id=223547538732703
"""

def findEncryptedWord(S):
    n = len(S)
    mid = n//2
    if n % 2 == 0:
        mid -= 1
    if n < 1:
        return ""
    return S[mid] + findEncryptedWord(S[0:mid]) + findEncryptedWord(S[mid+1:])


test("bac",findEncryptedWord("abc"))
test("bacd",findEncryptedWord("abcd"))
test("xbacbca", findEncryptedWord("abcxcba"))
test("", findEncryptedWord(""))
test("eafcobok",findEncryptedWord("facebook"))
