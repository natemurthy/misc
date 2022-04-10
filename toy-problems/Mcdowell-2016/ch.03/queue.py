class Queue:

    class QNode:
        def __init__(self, x):
            self.data = x
            self.next = None

    def __init__(self):
        self.first = self.last = None
        self.size = 0

    def add(self, x):
        n = self.QNode(x)
        if self.last:
            self.last.next = n
        self.last = n
        if self.first is None:
            self.first = self.last

        self.size += 1

    def remove(self):
        if self.first is None:
            return None
        data = self.first.data
        self.first = self.first.next
        if self.first is None:
            self.last = None
        return data

    def peek(self):
        if self.first is None:
            return None
        return self.first.data

    def is_empty(self):
        return first is None

    def pprint(self):
        s = ""
        first = self.first
        while first:
            s += "{} ".format(first.data)
            first = first.next
        print s



q = Queue()
q.add(1)
q.add(2)
q.add(3)
q.add(4)
q.add(5)
q.pprint()

print ""
print q.peek()
print q.remove()
print q.remove()
print q.remove()
q.pprint()
