import com.tinkerpop.blueprints._
import com.tinkerpop.blueprints.impls.orient._
import collection.JavaConversions._

object Examples extends App {

  val factory = new OrientGraphFactory("remote:/localhost/graph-db").setupPool(1,10)

  def example1 = {
    val graph = factory.getTx
    graph.addVerex() // works, but throws deprecation warning
    graph.addVertex(null) // fails in scala, but works in java. why?
    graph.commit
  }

  def example2 = ???

  def example3 = ???

  def main(args:Array[String]) {
  
  }

}
