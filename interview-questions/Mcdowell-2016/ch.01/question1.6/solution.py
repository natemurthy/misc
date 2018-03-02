#!/usr/bin/python
# -*- coding: utf-8 -*-

import unittest


# My solution
def compress_string(phrase):
    s = list(phrase)
    compressed = []
    char_count = 1
    for i in range(0, len(s)-1):
        if s[i] == s[i+1]:
            char_count += 1
        else:
            compressed.append(s[i])
            compressed.append(str(char_count))
            char_count = 1
        if i+1 == len(s)-1:
            compressed.append(s[i+1])
            compressed.append(str(char_count))
    if len(compressed) > len(s):
        return phrase
    return ''.join(compressed)


class SolutionTest(unittest.TestCase):

    def test_is_one_away(self):
        self.assertEqual(compress_string("aaabbb"), "a3b3")
        self.assertEqual(compress_string("xxxyyyyuuzzcccd"), "x3y4u2z2c3d1")
        self.assertEqual(compress_string("ab"), "ab")

if __name__ == '__main__':
    unittest.main()
