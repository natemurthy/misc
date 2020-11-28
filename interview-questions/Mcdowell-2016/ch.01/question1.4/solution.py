#!/usr/bin/python
# -*- coding: utf-8 -*-

import unittest


# Naïve solution, does not scale because of factorial complexity of permutations func
# This becomes infeasible around 10 to 15 characters, instead do a character count
def is_permutation_of_palindrome_naive(phrase):
    from itertools import permutations
    nospaces = [c for c in phrase if c != ' ']
    perms = set([''.join(p) for p in permutations(nospaces)])
    for p in perms:
        if p == p[::-1]:
            return True
            break
    return False


# Better solution which is guaranteeably O(N) and more efficient than above
def is_permutation_of_palindrome_better(phrase):
    import collections
    nospaces = [c for c in phrase if c != ' ']
    counts = collections.defaultdict(int)

    for c in nospaces:
        counts[c] += 1

    if len(nospaces) % 2 == 0:
        for v in counts.values():
            if v % 2 == 1:
                return False
        return True
    else:
        odd_char_count = 0
        for v in counts.values():
            if v % 2 == 1:
                odd_char_count += 1
        if odd_char_count != 1:
            return False
        return True


class SolutionTest(unittest.TestCase):

    def test_naive(self):
        self.assertTrue(is_permutation_of_palindrome_naive("taco cat"))

    def test_better(self):
        self.assertTrue(is_permutation_of_palindrome_better("no specific epson"))

if __name__ == '__main__':
    unittest.main(verbosity=2)
