#!/bin/env python

def test(expected, actual):
    if expected == actual:
        print("Pass")
    else:
        print("Fail (expected '{}', actual '{}')".format(expected, actual))


"""
Number of Visible Nodes
https://www.facebookrecruiting.com/portal/coding_practice_question/?problem_id=495004218121393

Seems like this problem is just asking for number levels in the tree, which should be equivalent
to the number of left-most visible nodes
"""
class TreeNode:
    def __init__(self, key):
        self.val = key
        self.left = None
        self.right = None

def visible_nodes(root):
    if root is None:
        return 0
    levels, curr = [], [root]
    while curr:
        next_level, vals = [], []
        for node in curr:
            vals.append(node.val)
            if node.left:
                next_level.append(node.left)
            if node.right:
                next_level.append(node.right)
        levels.append(vals)
        curr = next_level
    return len(levels)

root_1 = TreeNode(8)
root_1.left = TreeNode(3)
root_1.right = TreeNode(10)
root_1.left.left = TreeNode(1)
root_1.left.right = TreeNode(6)
root_1.left.right.left = TreeNode(4)
root_1.left.right.right = TreeNode(7)
root_1.right.right = TreeNode(14)
root_1.right.right.left = TreeNode(13)
expected_1 = 4
output_1 = visible_nodes(root_1)
test(expected_1, output_1)

root_2 = TreeNode(10)
root_2.left = TreeNode(8)
root_2.right = TreeNode(15)
root_2.left.left = TreeNode(4)
root_2.left.left.right = TreeNode(5)
root_2.left.left.right.right = TreeNode(6)
root_2.right.left =TreeNode(14)
root_2.right.right = TreeNode(16)

expected_2 = 5
output_2 = visible_nodes(root_2)
test(expected_2, output_2)
