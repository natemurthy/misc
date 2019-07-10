import java.util.*;
import java.util.concurrent.*;

// Implement a special hash map:
// put
// get
// delete
// getRandom, returns a random value from the map with uniform probability for every value
//
class SpecialHashMap<K, V> extends ConcurrentHashMap<K,V> {

    private List<K> keys;

    public SpecialHashMap() {
        super();
        // see https://bigocheatsheet.io/ for selecting
        keys = new LinkedList<K>();
    }

    @Override
    public V get(Object key) {
        return super.get(key);
    }

    @Override
    public V put(K key, V value) {
        if (!keys.contains(key)) {
            keys.add(key);
        }
        return super.put(key, value);
    }

    @Override
    public V remove(Object key) {
        keys.remove(key);
        return super.remove(key);
    }

    public V getRandom() {
        int ix = (int)(Math.random()*keys.size());
        return super.get(keys.get(ix));
    }
}


class Solution {
  public static void main(String[] args) {
    SpecialHashMap<Integer,String> map = new SpecialHashMap<Integer,String>();
    
    map.put(1,"one");
    map.put(2,"two");
    map.put(3,"three");
    map.put(4,"four");
    map.put(5,"five");
    map.put(6,"six");
    map.put(7,"seven");
    map.put(8,"eight");
    System.out.println(map.getRandom());

    map.remove(1);
    System.out.println(map.get(1));
  }
}

