import com.orientechnologies.orient.`object`.db.OObjectDatabaseTx
import com.tinkerpop.blueprints._
import com.tinkerpop.blueprints.impls.orient._
import collection.JavaConversions._
import javax.persistence.{Version, Id}


object Examples extends App {
  
  implicit def orientDbResource[A <: OrientGraph] = new Resource[A] {
    override def close(r:A) = r.shutdown()
  }

  val factory = new OrientGraphFactory("remote:/localhost/graph-db").setupPool(1,10)
  val graph = factory.getTx
  def example1 = {
    graph.addVerex()        // throws deprecation warning
    graph.addVertex(null)   // fails in scala, but works in java. why?
    // Can anyone guess how to do this in Scala?
  }

  def example2 = {
    // committing this record throws "ODatabaseException: Error on deserialization of Serializable"
    case class Foo(a:Int,b:String)
    val f = new Foo(12,"twelve")
    val v = graph.addVertex()
    v.setProperty("record",f)
  } 

  def example3 = {
    // maybe orientdb's scala example will work
    case class Foo(a:Int,b:String) { @Id var id: String = _; @Version var version: String = _ }
    val uri = "remote:localhost/graph-db"
    val db = new OObjectDatabaseTx(uri)
    db.open("admin","admin")                              // ClassCastException: OObjectDatabaseTx cannot be cast to scala.runtime.Nothing$
    db.getEntityManager.registerEntityClass(classOf[Foo]) // java.lang.Class.getSimpleName throws Malformed class name
    val f = new Foo(12,"twelve")
    db.save(f)
  }

  try {
    example1
    example2
    example3
    graph.commit
  } finally {
    graph.shutdown 
  }

}
