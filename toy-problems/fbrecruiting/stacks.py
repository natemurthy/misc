#!/bin/env python

def test(expected, actual):
    if expected == actual:
        print("Pass")
    else:
        print("Fail (expected '{}', actual '{}')".format(expected, actual))


"""
Balance Brackets
https://www.facebookrecruiting.com/portal/coding_practice_question/?problem_id=211548593612944
"""

def matching(l, r):
    if l == '[' and r == ']':
        return True
    if l == '(' and r == ')':
        return True
    if l == '{' and r == '}':
        return True
    return False


def isBalanced(s):
    st = []
    for c in s:
        if c == '[' or c =='(' or c=='{':
            # add all the opening chars
            st.append(c)
        elif c == ']' or c == ')' or c == '}':
            # if we see a closing char and the stack of opening chars
            # is empty, we know the brackets are unbalanced
            if len(st) == 0:
                return False
            # pop the top opening element in the stack and compare
            # it to the closing character c
            top = st.pop()
            if not matching(top, c):
                return False
    # the stack will be non empty if there are any opening chars
    # that remain unbalanced with any closing chars
    if len(st) != 0:
        return False
    return True




s1 = "{[(])}"
expected_1 = False
output_1 = isBalanced(s1)
test(expected_1, output_1)

s2 = "{{[[(())]]}}"
expected_2 = True
output_2 = isBalanced(s2)
test(expected_2, output_2)

test(True, isBalanced("{123(456[.768])}"))
