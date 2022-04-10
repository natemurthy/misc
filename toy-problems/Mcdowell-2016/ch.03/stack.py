class Stack:

    class StackNode:
        def __init__(self, x):
            self.data = x
            self.under = None

    def __init__(self):
        self.top = None
        self.size = 0
        self.min_element = None

    def push(self, x):
        n = self.StackNode(x)
        n.under = self.top
        self.top = n

        if self.min_element is None or x < self.min_element:
            self.min_element = x

    def peek(self):
        return self.top

    def pop(self):
        # TODO update min_element if smallest value is popped from stack
        if self.top is None:
            return None
        else:
            tmp = self.top
            self.top = tmp.under
            return tmp.data

    def is_empty(self):
        return self.top is None

    def min(self):
        # for question 3.2
        return self.min_element

    def pprint(self):
        top = self.top
        while top:
            print top.data
            top = top.under


#s = Stack()
#s.push(1)
#s.push(2)
#s.push(3)
#s.push(-9)
#s.pprint()

#print ""
#s.pop()
#s.pop()
#s.pop()
#s.pop()
#s.pop()
#s.pprint()

#print s.peek()

#print ""
#print s.pop()

#print ""
#s.pprint()


