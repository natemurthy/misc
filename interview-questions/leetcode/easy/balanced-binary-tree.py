"""
https://leetcode.com/problems/balanced-binary-tree/

Given a binary tree, determine if it is height-balanced.

For this problem, a height-balanced binary tree is defined as: a binary tree
in which the left and right subtrees of every node differ in height by no more than 1.
"""

class TreeNode:
    def __init__(self, x):
        self.val = x
        self.left = self.right = None

def is_balanced(t):
    return get_height(t) >= 0

def get_height(t):
    if t is None:
        return 0
    left_height = get_height(t.left)
    right_height = get_height(t.right)
    
    # identical to max_depth except we compare the left/right heights
    if left_height < 0 or right_height < 0 or abs(left_height-right_height) > 1:
        return -1
    
    return max(left_height, right_height)+1

def max_depth(t):
    if t is None:
        return 0
    left_height = max_depth(t.left)
    right_height = max_depth(t.right)
    return max(left_height, right_height)+1
    

root = TreeNode(2)
root.left = TreeNode(1)
root.right = TreeNode(3)
root.right.right = TreeNode(4)
print max_depth(root)
print is_balanced(root)
