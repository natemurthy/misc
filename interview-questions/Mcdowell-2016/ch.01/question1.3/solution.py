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
    #unittest.main()
    p="Following the massive, 20,000-person walkout at Google in November, Google got rid of forced arbitration for sexual harassment and sexual assault claims, offering more transparency around those investigations and more."
    print urlify(p, len(p))
