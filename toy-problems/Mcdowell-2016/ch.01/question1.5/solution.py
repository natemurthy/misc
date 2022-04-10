#!/usr/bin/python
# -*- coding: utf-8 -*-

import unittest


# My solution
def is_one_away(phrase1, phrase2):
    edit_count = len(phrase1)
    for c in phrase1:
        if c in phrase2:
            edit_count -= 1
    if edit_count > 1:
        return False
    return True


class SolutionTest(unittest.TestCase):

    def test_is_one_away(self):
        self.assertTrue( is_one_away("pale" , "ple"))
        self.assertTrue( is_one_away("pales", "pale"))
        self.assertTrue( is_one_away("pale" , "bale"))
        self.assertFalse(is_one_away("pale" , "bake"))

if __name__ == '__main__':
    unittest.main()
