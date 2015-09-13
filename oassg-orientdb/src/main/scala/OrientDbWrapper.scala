import com.tinkerpop.blueprints._
import com.tinkerpop.blueprints.impls.orient._
import collection.JavaConversions._
import javax.persistence.{Version, Id}
import org.json4s._
import org.json4s.jackson.JsonMethods
import resource._

object OrientDbWrapper {

  implicit def objectGraphMapper(graph: OrientGraph) = new ObjectGraphMapper(graph)

  final class ObjectGraphMapper(graph: OrientGraph) extends AnyVal {
    
    def objectVertexMapper[T:TypeTag](id: String) = {
      implicit val readFormats = DefaultFormats
      val getFromDb = 
        graph.getVertices("record_id",id).toList.headOption
          .map(_.getProperty("as_json").asInstanceOf[String])
          .map(JsonMethods.parse)
      }
      typeOf[T] match {
        case t if t =:= typeOf[Foo] => getFromDb.map(_.extract[Foo].asInstanceOf[T])
        case t if t =:= typeOf[Bar] => getFromDb.map(_.extract[Bar].asInstanceOf[T])
        case _ => None
      }
    }
    
     def objectEdgeMapper[T:TypeTag](id: String) = {
      implicit val readFormats = DefaultFormats
      val getFromDb = 
        graph.getEdges("record_id",id).toList.headOption
          .map(_.getProperty("as_json").asInstanceOf[String])
          .map(JsonMethods.parse)
      }
      typeOf[T] match {
        case t if t =:= typeOf[Bippity] => getFromDb.map(_.extract[Bippity].asInstanceOf[T])
        case t if t =:= typeOf[Boppity] => getFromDb.map(_.extract[Boppity].asInstanceOf[T])
        case _ => None
      }
    }
    
  }

}

// Vertex classes
case class Foo(a:Int, b:String)
case class Bar(color:String,price:Double)

// Edge classes
case class Bippity(x:Int,y:Int)
case class Boppity(r1:String,r2:String)
