#!/usr/bin/python
# -*- coding: utf-8 -*-

import unittest


# My solution
def has_all_unique_chars(input_str):
    char_counts = dict()
    for c in input_str:
        try:
            char_counts[c] += 1
        except:
            char_counts[c] = 1
    return len(filter(lambda v: v > 1, char_counts.values())) == 0


class SolutionTest(unittest.TestCase):

    def test_has_all_unique_chars(self):
        self.assertTrue(has_all_unique_chars('uniq'))
        self.assertFalse(has_all_unique_chars('non-unique'))

if __name__ == '__main__':
    unittest.main()
