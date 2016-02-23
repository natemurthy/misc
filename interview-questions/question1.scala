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
