
import org.json4s._, org.json4s.jackson.JsonMethods

object `json4s-booleans-oops` {

case class Person(active:Boolean,name:String)

object Person {
	import scala.util.Try
	def apply(active:String,name:String): Person = Person(
			Try(active.toBoolean).getOrElse(false),
			name
		)
}

implicit val formats = DefaultFormats
val p = JsonMethods.parse(""" {"active":"false","name":"bridget"} """)

p.extract[Person]
// throws org.json4s.package$MappingException: No usable value for active
// Do not know how to convert JString(false) into boolean

}
