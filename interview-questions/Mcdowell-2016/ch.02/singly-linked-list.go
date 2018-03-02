package main

import (
	"bytes"
	"fmt"
)

// Node of a linked list
type Node struct {
	Data interface{}
	Next *Node
}

// LinkedList implementation
type LinkedList struct {
	root   *Node
	length int
}

// Insert node at the head of the list
func (l *LinkedList) Insert(n *Node) {
	n.Next = l.root
	l.root = n
	l.length++
}

// AppendToTail of this list
func (l *LinkedList) AppendToTail(end *Node) {
	if l.root == nil {
		l.root = end
		l.length++
		return
	}
	n := l.root
	for n.Next != nil {
		n = n.Next
	}
	n.Next = end
	l.length++
}

func (l *LinkedList) String() string {
	var buff bytes.Buffer
	buff.WriteString("[")
	for at := l.root; at != nil; at = at.Next {
		buff.WriteString(fmt.Sprintf("%v, ", at.Data))
	}
	buff.Truncate(buff.Len() - 2)
	buff.WriteString("]")
	return buff.String()
}

func main() {
	n1 := Node{Data: 1}
	n2 := Node{Data: 2}
	n3 := Node{Data: 3}

	list := LinkedList{}
	list.Insert(&n1)
	list.Insert(&n2)
	list.Insert(&n3)
	fmt.Println(list.String())

	list2 := LinkedList{}
	list2.AppendToTail(&n1)
	list2.AppendToTail(&n2)
	list2.AppendToTail(&n3)
	fmt.Println(list2.String())
}
