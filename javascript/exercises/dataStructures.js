// Arrays

var arr = ["a", "b", "c", "g", "d", "e"]

// access
// returns the value "g" indexed at i=3
arr[3]

// search
// returns "yes" if the letter "g" is found, "no" otherwise
arr.forEach(e => e == "g" ? "yes" : "no")
// returns the index of the first occurrence of the letter "g", -1 otherwise
arr.indexOf("g")

// insert
// add an element to the end of the array
arr.push("f")

// delete
// remove an element from the of the array
arr.pop()




// Linked Lists
// Traversy Media: https://www.youtube.com/watch?v=ZBdE8DElQQU
// Git: https://gist.github.com/bradtraversy/c38f029e5f9e56a19c393d3a3b1e1544

class Node {
  constructor(data, next = null) {
    this.data = data;
    this.next = next;
  }
}

class LinkedList {
  constructor() {
    this.head = null;
    this.size = 0;
  }

  insertFirst(data) {
    this.head = new Node(data, this.head)
    this.size++
  }

  insertLast(data) {
    let node = new Node(data)
    let current
    if (!this.head) { 
      this.head = node
    } else {
      current = this.head
      while (current.next) {
        current = current.next
      }
      current.next = node
    }
    this.size++
  }

  insertAt(data, index) {
    if 
  }

  print() {
    let current = this.head
    while (current) {
      console.log(current.data)
      current = current.next
    }
  }
}

const ll = new LinkedList()
ll.insertFirst(100)
ll.insertFirst(200)
ll.insertFirst(300)
ll.insertLast(400)

console.log(ll)
ll.print()




// Stacks

// Hash Table / Map / Dictionaries

// Trees

// Graphs
