import com.tinkerpop.blueprints._, impls.orient._
import org.json4s._,  org.json4s.jackson.JsonMethods
import org.json4s.jackson.Serialization, Serialization.write


object Example2 {

implicit val readFormats = DefaultFormats
implicit val writeFormats = Serialization.formats(NoTypeHints)

case class Person(id:String,name:String,age:Int)
case class Animal(id:String,species:String)

val p0 = Person("person-0","Adam",33)
val p1 = Person("person-1","Abby",22)
val p2 = Person("person-2","John",47)
val p3 = Person("person-3","Jane",19)
val p4 = Person("person-4","Flin",56)

val a0 = Animal("animal-0","Pig")
val a1 = Animal("animal-1","Pig")
val a2 = Animal("animal-2","Bird")

val graph = new OrientGraph("remote:/localhost/graph-db")

val v0 = graph.addVertex("class:Person",Nil:_*); v0.setProperty("person_id",p0.id); v0.setProperty("as_json",write(p0))
val v1 = graph.addVertex("class:Person",Nil:_*); v1.setProperty("person_id",p1.id); v1.setProperty("as_json",write(p1))
val v2 = graph.addVertex("class:Person",Nil:_*); v2.setProperty("person_id",p2.id); v2.setProperty("as_json",write(p2))
val v3 = graph.addVertex("class:Person",Nil:_*); v3.setProperty("person_id",p3.id); v3.setProperty("as_json",write(p3))
val v4 = graph.addVertex("class:Person",Nil:_*); v4.setProperty("person_id",p4.id); v4.setProperty("as_json",write(p4))
val v5 = graph.addVertex("class:Animal",Nil:_*); v5.setProperty("animal_id",a0.id); v5.setProperty("as_json",write(a0))
val v6 = graph.addVertex("class:Animal",Nil:_*); v6.setProperty("animal_id",a1.id); v6.setProperty("as_json",write(a1))
val v7 = graph.addVertex("class:Animal",Nil:_*); v7.setProperty("animal_id",a2.id); v7.setProperty("as_json",write(a2))

graph.addEdge("class:Infection",v7,v6,"infected")
graph.addEdge("class:Infection",v7,v5,"infected")
graph.addEdge("class:Infection",v5,v4,"infected")
graph.addEdge("class:Infection",v4,v3,"infected")
graph.addEdge("class:Infection",v4,v2,"infected")
graph.addEdge("class:Infection",v4,v1,"infected")
graph.addEdge("class:Infection",v1,v0,"infected")

graph.commit

}
