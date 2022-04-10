"""
https://stackoverflow.com/questions/34012886/print-binary-tree-level-by-level-in-python
"""

class BstNode:

    def __init__(self, data):
        self.data = data
        self.right = None
        self.left = None

    def insert_order_sorted(self, data):
        if self.data == data:
            return
        elif self.data is None:
            self.data = data
        elif self.data < data:
            if self.right is None:
                self.right = BstNode(data)
            else:
                self.right.insert_order_sorted(data)
        else:
            if self.left is None:
                self.left = BstNode(data)
            else:
                self.left.insert_order_sorted(data)

    def insert_order_level(self, data):
        if not self.data:
            self.data = data
            return
        q = []
        q.append(self)
        while q:
            temp = q.pop(0)
            if not temp.left:
                temp.left = BstNode(data)
                break
            else:
                q.append(temp.left)
            if not temp.right:
                temp.right = BstNode(data)
                break
            else:
                q.append(temp.right)
        

    def display(self):
        lines, *_ = self._display_aux()
        for line in lines:
            print(line)

    def _display_aux(self):
        """Returns list of strings, width, height, and horizontal coordinate of the root."""
        # No child.
        if self.right is None and self.left is None:
            line = '%s' % self.data
            width = len(line)
            height = 1
            middle = width // 2
            return [line], width, height, middle

        # Only left child.
        if self.right is None:
            lines, n, p, x = self.left._display_aux()
            s = '%s' % self.data
            u = len(s)
            first_line = (x + 1) * ' ' + (n - x - 1) * '_' + s
            second_line = x * ' ' + '/' + (n - x - 1 + u) * ' '
            shifted_lines = [line + u * ' ' for line in lines]
            return [first_line, second_line] + shifted_lines, n + u, p + 2, n + u // 2

        # Only right child.
        if self.left is None:
            lines, n, p, x = self.right._display_aux()
            s = '%s' % self.data
            u = len(s)
            first_line = s + x * '_' + (n - x) * ' '
            second_line = (u + x) * ' ' + '\\' + (n - x - 1) * ' '
            shifted_lines = [u * ' ' + line for line in lines]
            return [first_line, second_line] + shifted_lines, n + u, p + 2, u // 2

        # Two children.
        left, n, p, x = self.left._display_aux()
        right, m, q, y = self.right._display_aux()
        s = '%s' % self.data
        u = len(s)
        first_line = (x + 1) * ' ' + (n - x - 1) * '_' + s + y * '_' + (m - y) * ' '
        second_line = x * ' ' + '/' + (n - x - 1 + u + y) * ' ' + '\\' + (m - y - 1) * ' '
        if p < q:
            left += [n * ' '] * (q - p)
        elif q < p:
            right += [m * ' '] * (p - q)
        zipped_lines = zip(left, right)
        lines = [first_line, second_line] + [a + u * ' ' + b for a, b in zipped_lines]
        return lines, n + m + u, max(p, q) + 2, n + u // 2


def insert_level_order(arr, root, i, n):
    if i < n:
        temp = BstNode(arr[i])
        root = temp
        root.left = insert_level_order(arr, root.left, 2*i+1, n)
        root.right = insert_level_order(arr, root.right, 2*i+2, n)
    return root



def rand_int(v):
    import random
    return random.randint(0, v*2)

n = 6
b = BstNode(rand_int(n))

#for _ in range(n):
    #b.insert_order_sorted(rand_int(n))
#b.display()

for _ in range(n):
    b.insert_order_level(rand_int(n))
b.display()

#arr = [0,1,2]
#t = None
#t = insert_level_order(arr, t, 0, n)
#t.display()

