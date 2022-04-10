class Node:

    def __init__(self,data):
        self.data = data
        self.next = None


class LinkedList:
    
    def __init__(self):
        self.head = None
        self.size = 0

    def insert(self,data):
        n = Node(data)
        n.next = self.head
        self.head = n
        self.size+=1

    def find(self, pos):
        cur = self.head

        if pos < 0 or pos > self.size-1:
            return

        if cur is None:
            return

        #if pos == 0:
            #return cur

        for i in range(pos):
            cur = cur.next
            if cur.next is None:
                break

        return cur 

    def delete_at(self, pos):
        cur = self.head

        if pos < 0 or pos > self.size-1:
            return

        if cur is None:
            return

        if pos == 0:
            self.head = cur.next
            return

        for _ in range(pos-1):
            cur = cur.next
            if cur is None:
                break
           
        next = cur.next.next
        cur.next = next

    def delete(self, v):
        cur = self.head

        if cur is None:
            return

        if cur.data == v:
            self.head = cur.next

        while True:
            peek = cur.next
            if peek is None or peek.data == v:
                break
            cur = peek

        if cur.next is None:
            next = None
        else:
            next = cur.next.next

        cur.next = next

    def merge(self, r):
        cur = self.head

        if r is None:
            return

        if r.head is None:
            return

        if cur is None:
            cur = r.head
            return
        
        while cur.next:
            cur = cur.next
        
        cur.next = r.head
       
    def reverse(self):
        prev = None
        curr = self.head

        while curr:
            next = curr.next
            curr.next = prev

            prev = curr
            curr = next

        self.head = prev

    def _print(self):
        cur = self.head
        i = 0
        while cur:
            print i, cur.data
            cur = cur.next
            i += 1


if __name__ == "__main__":
    l =  LinkedList()
    l.insert('foo')
    l.insert('bar')
    l.insert('baz')
    l.insert('dog')
    print "print linked list"
    l._print()

    print ""

    print "find node @ pos=0"
    print l.find(0).data

    print ""

    print "reverse list"
    l.reverse()
    l._print()

    print ""

    print "delete node @ pos=0"
    l.delete_at(0)
    l._print()

    print ""

    print "delete node where data='foo'"
    l.delete('foo')
    l._print()

    print ""

    r  = LinkedList()
    r.insert('aaa')
    r.insert('bbb')
    r.insert('ccc')

    print "merge linked lists"
    l.merge(r)
    l._print()
