from dataclasses import dataclass

from typing import Any


class Node:
    def __ini__(self, val: int, next: Any):
        self.val = val
        self.next = next

@dataclass
class ListNode(Node):
    val: int
    next: Node | None = None

example1 = ListNode(val=1, next=ListNode(1, next=ListNode(2)))

example2 = ListNode(val=1, next=ListNode(1, next=ListNode(2, next=ListNode(3, next=ListNode(3)))))


def traverse(n: Node):
    while n:
        print(n.val)
        n = n.next


def remove_dups(n: Node):
    while n is not None:
        second = n
        #print(n.val, second.val)
        while n.next is not None:
            #print(n.val)
            if n.val == n.next.val:
                #print(f"{n.val} == {n.next.val}")
                second.next = second.next.next
            elif second.next is not None:
                second = second.next
            else:
                break
        n = second = n.next



print("example1")
traverse(example1)
remove_dups(example1)
traverse(example1)

print()
print("example2")
traverse(example2)
remove_dups(example1)
traverse(example1)
