import com.hazelcast.core._

/**
 * Try this out on each machine with different
 * k,v pair insertions
 */
object Example {
  val dCache = Hazelcast.newHazelcastInstance()
  val kvPairs: java.util.Map[Int,String] = dCache.getMap("kv-pairs")
  kvPairs.put(1,"one")
  kvPairs.size
}
