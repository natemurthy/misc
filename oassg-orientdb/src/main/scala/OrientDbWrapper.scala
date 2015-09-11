import com.tinkerpop.blueprints._
import com.tinkerpop.blueprints.impls.orient._
import collection.JavaConversions._
import javax.persistence.{Version, Id}
import resource._

object OrientDbWrapper {

  implicit def objectGraphMapper(graph: OrientGraph) = new ObjectGraphMapper(graph)

  final class ObjectGraphMapper(graph: OrientGraph) extends AnyVal {
    def objectGraphMapper[T:TypeTag](id: String) = {
      val getFromDb = (recordId:String) => {
        graph.getVertices("record_id",recordId).toList.headOption
          .getProperty("as_json").asInstanceOf[String]
      }
      typeOf[T] match {
        case t if t =:= typeOf[Foo] => Some(t)
        case t if t =:= typeOf[Bar] => Some(t)
        case _ => None
      }
    }
  }

}

case class Foo(a:Int, b:String)
case class Bar(color:String,price:Double)
