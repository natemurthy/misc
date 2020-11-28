#!/bin/env python


class Node:
    def __init__(self, v):
        self.data = v
        self.next = None

    def __repr__(self):
        if self:
            return "{} -> {}".format(self.data, self.next)

class LinkedList:
    def __init__(self):
        self.head = None

    def insert(self, v):
        n = Node(v)
        n.next = self.head
        self.head = n

    def prepend(self, v):
        self.insert(v)

    def append(self, v):
        n = Node(v)
        if self.head is None:
            self.head = n
            return

        cur = self.head
        while cur.next:
            cur = cur.next
        cur.next = n

    def dedup_sorted(self):
        cur = self.head
        while cur:
            runner = cur.next
            while runner and (cur.data == runner.data):
                runner = runner.next
            cur.next = runner
            cur = runner

    def dedup_unsorted(self):
        cur = self.head
        seen = []
        while cur:
            if cur.data not in seen:
                seen.append(cur.data)
            runner = cur.next
            while runner and (runner.data in seen):
                runner = runner.next
            cur.next = runner
            cur = runner

    def pprint(self):
        print self.head


l1 = LinkedList()
l1.prepend(1)
l1.prepend(1)
l1.prepend(1)
l1.prepend(2)
l1.prepend(2)
l1.prepend(2)
l1.prepend(2)
l1.prepend(3)
l1.prepend(3)
l1.prepend(3)
l1.pprint()
l1.dedup_sorted()
l1.pprint()

print ""

l2 = LinkedList()
l2.append(1)
l2.append(1)
l2.append(1)
l2.append(2)
l2.append(2)
l2.append(2)
l2.append(2)
l2.append(3)
l2.append(3)
l2.append(3)
l2.pprint()
l2.dedup_sorted()
l2.pprint()

print ""

l3 = LinkedList()
l3.prepend(1)
l3.prepend(1)
l3.prepend(2)
l3.prepend(1)
l3.prepend(0)
l3.prepend(-234)
l3.prepend(1)
l3.prepend(2)
l3.pprint()
l3.dedup_unsorted()
l3.pprint()
