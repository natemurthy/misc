#!/usr/bin/python
# -*- coding: utf-8 -*-

import unittest


# My solution
def urlify(phrase, phrase_length):
    s = list(phrase[:phrase_length])
    for i in range(0,phrase_length):
        if s[i] == ' ':
            s[i] = '%20'
    return ''.join(s)

class SolutionTest(unittest.TestCase):

    def test_is_one_away(self):
        self.assertEqual(
                urlify("mr john smith   ", 13),
                "mr%20john%20smith")

if __name__ == '__main__':
    unittest.main()
