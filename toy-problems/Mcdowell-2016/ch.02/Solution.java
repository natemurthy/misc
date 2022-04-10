class Element {
    Element next = null;
    int data;

    public Element(int d) {
        data = d;
    }
}

class List {
    Element root = null;
    int len = 0;
    
    public List() {}

    void appendToTail(int d) {
        Element end = new Element(d);
        if (root == null) {
            root = end;
            len++;
            return;
        }
        Element n = root;
        while (n.next != null) {
            n = n.next;
        }
        n.next = end;
        len++;
    }

    void traverse() {
        Element n = root;
        while (n.next != null) {
            System.out.println(n.data);
            n = n.next;
        }
        System.out.println(n.data);
    }
}

public class Solution {

    public static void main(String [] args) {
        List l = new List();
        l.appendToTail(1);
        l.appendToTail(2);
        l.appendToTail(3);
        l.traverse();
        System.out.println("size: " + l.len);
    }
}
