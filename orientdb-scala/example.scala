import com.tinkerpop.blueprints.impls.orient._, com.tinkerpop.blueprints._
import collection.JavaConverters._
//import collection.JavaConversions._

object example {

val graph =  new OrientGraph("remote:/localhost/grid-topology")

val m0 = graph.addVertex(null,Nil: _*); m0.setProperty("name","substation"); m0.setProperty("net_load",130.1)
val m1 = graph.addVertex(null,Nil: _*); m1.setProperty("name","submeter-1"); m1.setProperty("net_load",25.9)
val m2 = graph.addVertex(null,Nil: _*); m2.setProperty("name","submeter-2"); m2.setProperty("net_load",71.4)
val m3 = graph.addVertex(null,Nil: _*); m3.setProperty("name","submeter-3"); m3.setProperty("net_load",32.8)
graph.addEdge(null,m0,m1,"is parent of")
graph.addEdge(null,m0,m2,"is parent of")
graph.addEdge(null,m0,m3,"is parent of")
graph.commit

val allVertices = graph.getVertices.asScala.toList
//val allVertices = graph.getVertices.toList

val substations = allVertices.filter(_.getProperty("name").asInstanceOf[String]=="substation")
val submeters = allVertices.filter(_.getProperty("name").asInstanceOf[String].contains("submeter"))

submeters.map(_.getProperty("net_load").asInstanceOf[Double]).foldLeft(0.0)(_+_)

val substation = substations(0)
substation.getVertices(Direction.OUT).asScala

// using SQL commands
import com.orientechnologies.orient.core.sql.OCommandSQL
graph.command(new OCommandSQL("SELECT FROM V")).execute().asInstanceOf[java.lang.Iterable[Vertex]].asScala.toList

}
