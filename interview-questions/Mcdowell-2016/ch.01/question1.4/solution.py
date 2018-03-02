#!/usr/bin/python
# -*- coding: utf-8 -*-

import unittest


# My solution
def is_palindrome_permutations(phrase):
    from itertools import permutations
    perms = set([''.join(p) for p in permutations(phrase)])
    for p in perms:
        if p == p[::-1]:
            print p
            return True
            break
    return False


class SolutionTest(unittest.TestCase):

    def test_is(self):
        self.assertTrue(is_palindrome_permutations("taco cat"))

if __name__ == '__main__':
    unittest.main(verbosity=2)
