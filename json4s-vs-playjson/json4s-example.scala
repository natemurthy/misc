import org.json4s._, org.json4s.JsonDSL._, org.json4s.jackson.JsonMethods

object `json4s-example` extends App {

val content = """
{
  "name" : "Watership Down",
  "location" : {
    "lat" : 51.235685,
    "long" : -1.309197
  },
  "residents" : [ {
    "name" : "Fiver",
    "age" : 4,
    "role" : null
  }, {
    "name" : "Bigwig",
    "age" : 6,
    "role" : "Owsla"
  } ]
}
"""

// Converting to JValue
val json1 = JsonMethods.parse(content)

// Class creation of JValue
val json2 = 
  ("name" -> "Watership Down") ~
  ("location" -> ("lat" -> 51.235685)~("long" -> -1.309197)) ~
  ("residents" -> Seq(
    ( ("name" -> "Fiver") ~
      ("age" -> 4) ~
      ("role" -> null) ),
    ( ("name" -> "Bigwig") ~
      ("age" -> 6) ~
      ("role" -> "Owsla") )
    )
  )

case class Location(lat: Double, long: Double)
case class Resident(name: String, age: Int, role: Option[String])
case class Place(name: String, location: Location, residents: Seq[Resident])

// Writes
import org.json4s.jackson.Serialization, org.json4s.jackson.Serialization.{read, write}
implicit val writeFormats = Serialization.formats(NoTypeHints)
val place = Place(
  "Watership Down",
  Location(51.235685, -1.309197),
  Seq(
    Resident("Fiver", 4, None),
    Resident("Bigwig", 6, Some("Owsla"))
  )
)
val json3 = JsonMethods.parse(write(place))

// Reads
implicit val readFormats = DefaultFormats
val json = json3
json.extract[Place]
(json \ "location").extract[Location]
(json \ "residents").extract[List[Resident]]

println("runtime checks")

}