class TreeNode(object):
    def __init__(self, v, left=None, right=None):
        self.v = v
        self.left = left
        self.right = right


def inorder(t):
    if t.left:
        inorder(t.left)
    print t.v
    if t.right:
        inorder(t.right)

def preorder(t):
    print t.v
    if t.left:
        preorder(t.left)
    if t.right:
        preorder(t.right)

def postorder(t):
    if t.left:
        postorder(t.left)
    if t.right:
        postorder(t.right)
    print t.v

def find(t, k):
    
    if k < t.v:
        return find(t.left, k)

    if t is None or t.v == k:
        return t

    return find(t.right, k)

def insert(t, k):
    if t is None:
        return TreeNode(k)
    if k < t.v:
        t.left = insert(t.left, k)
    elif k > t.v:
        t.right = insert(t.right, k)
    return t


'''
       4
    2     6
 1      5   12
               18
 '''

if __name__ == "__main__":
    t = TreeNode(4, 
            TreeNode(2, TreeNode(1)),
            TreeNode(6, TreeNode(5), TreeNode(12, None, TreeNode(18)))
        )
    insert(t, 7)
    inorder(t)

'''
class Node(object):
    def __init__(self, key, left, right, parent):
        self.key = key
        self.left = left
        self.right = right
        self.parent = parent

def new_node(k):
    return Node(k, None, None, None)

def preorder_successor(root, n):
    
    if n.left:
        return n.left

    curr = n
    parent = curr.parent
    while (parent != None and parent.right == curr):
        curr = curr.parent
        parent = parent.parent

    if parent == None:
        return None

    return parent.right


root = new_node(20)
root.left = new_node(10)
root.left.parent = root
root.left.left = new_node(4);
root.left.left.parent = root.left;
root.left.right = new_node(18);
root.left.right.parent = root.left;
root.right = new_node(26);
root.right.parent = root;
root.right.left = new_node(24);
root.right.left.parent = root.right;
root.right.right = new_node(27);
root.right.right.parent = root.right;
root.left.right.left = new_node(14);
root.left.right.left.parent = root.left.right;
root.left.right.left.left = new_node(13);
root.left.right.left.left.parent = root.left.right.left;
root.left.right.left.right = new_node(15);
root.left.right.left.right.parent = root.left.right.left;
root.left.right.right = new_node(19);
root.left.right.right.parent = root.left.right;

print preorder_successor(root, root).key
'''
