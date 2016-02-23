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
