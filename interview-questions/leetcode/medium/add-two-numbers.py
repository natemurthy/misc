"""
https://leetcode.com/problems/add-two-numbers/

This is also a sample interview question from p.95 of Mcdowell-2016
"""

class Node:
    def __init__(self, data):
        self.data = data
        self.next = None

class LinkedList:
    def __init__(self):
        self.head = None
    
    def insert(self, data):
        n = Node(data)
        n.next = self.head
        self.head = n

    def pprint(self):
        cur = self.head
        s = ""
        while cur:
            if cur.next:
                s += "%s -> "%(cur.data)
            else:
                s += "%s"%(cur.data)
            cur = cur.next
        print s

def create_num(arr):
    l = LinkedList()
    i = len(arr)-1
    while i > -1:
        l.insert(arr[i])
        i-=1
    return l


def add_lists(l1, l2):
    sum_arr = []
    cur1 = l1.head
    cur2 = l2.head
    carry_over = 0
    while cur1 or cur2:
        d1, d2 = 0, 0
        # could also do some validation here to make sure digits are [0..9]
        if cur1:
            d1 = cur1.data
        if cur2:
            d2 = cur2.data

        v = d1 + d2 + carry_over

        if v > 9:
            carry_over = 1
            sum_arr.append(v % 10)
        else:
            carry_over = 0
            sum_arr.append(v)

        if cur1:
            cur1 = cur1.next
        if cur2:
            cur2 = cur2.next

        if (not cur1) and (not cur2) and carry_over:
            sum_arr.append(carry_over)

    return create_num(sum_arr)


l1 = create_num([2,4,3])
l1.pprint()
l2 = create_num([5,6,4])
l2.pprint()
add_lists(l1,l2).pprint()

print ""
l1 = create_num([0])
l1.pprint()
l2 = create_num([0])
l2.pprint()
add_lists(l1,l2).pprint()

print ""
l1 = create_num([9,9,9,9,9,9,9])
l1.pprint()
l2 = create_num([9,9,9,9])
l2.pprint()
add_lists(l1,l2).pprint()

print ""
l1 = create_num([7,1,6])
l1.pprint()
l2 = create_num([5,9,2])
l2.pprint()
add_lists(l1,l2).pprint()

print ""
l1 = create_num([5,5])
l1.pprint()
l2 = create_num([5,5])
l2.pprint()
add_lists(l1,l2).pprint()


