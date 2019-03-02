
class Tree:

    def __init__(self, v, left=None, right=None):
        self.v = v
        self.left = left
        self.right = right
    
    def __str__(self):
        return str(self.v)

    def bfs(self):

        visit = [(self, 0)]
        
        levels = dict()
        
        while visit:
            curr, level = visit.pop(0)
            if level not in levels:
                levels[level] = [curr]
            else:
                levels[level].append(curr)
            if curr.left:
                visit.append((curr.left, level+1))
            if curr.right:
                visit.append((curr.right, level+1))

        return levels


    def pretty_print(self):
        levels = self.bfs()
        
        spacing = []

        def in_order(node):
            if node.left:
                in_order(node.left)
            spacing.append(node.v)
            if node.right:
                in_order(node.right)

        in_order(self)

        for _, level in levels.items():
            s = []
            for i in range(len(spacing)):
                s.append(" ")
                for n in level:
                    if spacing[i] == n.v:
                        s[i] = str(n)
                
            print "".join(s)


'''
            1
        2          3
    6          4       5
    
'''
tree = Tree(1, left=Tree(2, left=Tree(6)), right=Tree(3, left=Tree(4), right=Tree(5)))

tree.pretty_print()

