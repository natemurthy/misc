/*
Quesiton 1

Given a linked list of integers whose length is a multiple of k, implement a method
that splits the linked list into sublists of length k, reverses each sublist, and then
combines the sublists into a whole linked list. For example:

    input: 1 -> 2 -> 3 -> 4 -> 5 -> 6
   output: 3 -> 2 -> 1 -> 6 -> 5 -> 4
*/

import collection.mutable.LinkedList

def seedLinkedList(ints: Iterable[Int], linkedList: LinkedList[Int] = null): LinkedList[Int] = {
  if (ints.size == 1)
    return LinkedList(ints.head)
  else {
    val newList = LinkedList(ints.head)
    newList.next = seedLinkedList(ints.tail, linkedList)
    return newList
  }
}

def reverseSplit(list: LinkedList[Int], k: Int): LinkedList[Int] = {
  if (list.length==k)
    list.reverse
  else {
    val splitList = list.splitAt(k)
    splitList._1.reverse ++ reverseSplit(splitList._2,k)
  }
}
