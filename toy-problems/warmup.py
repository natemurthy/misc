#!/bin/bash python


class TreeNode:
    def __init__(self, x):
        self.val = x
        self.left = None
        self.right = None


def level_order(t):
    if t is None:
        return []
    result, curr = [], [t]
    while curr:
        next_level, vals = [], []
        for node in curr:
            vals.append(node.val)
            if node.left:
                next_level.append(node.left)
            if node.right:
                next_level.append(node.right)
        result.append(vals)
        curr = next_level
    return result


def pprint(t):
    
    spacing = []

    def in_order(node):
        if node.left:
            in_order(node.left)
        spacing.append(node.val)
        if node.right:
            in_order(node.right)

    in_order(t)

    levels = level_order(t)

    for vals in levels:
        s = []
        for i in range(len(spacing)):
            s.append("  ")
            for v in vals:
                if spacing[i] == v:
                    s[i] = str(v)
            
        print "".join(s)




root = TreeNode(3)
root.left = TreeNode(9)
root.right = TreeNode(20)
root.right.left = TreeNode(15)
root.right.right = TreeNode(7)
root.right.right.right = TreeNode(888111998)
root.right.right.right.left = TreeNode(723847239472984)
root.right.right.right.right = TreeNode(385752387529875)

print(level_order(root))
pprint(root)



