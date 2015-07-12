import com.mongodb._, org.json4s._, org.json4s.jackson.JsonMethods._, org.json4s.mongo._

object example { 

implicit val formats = DefaultFormats

val mongoClient = new MongoClient("54.69.100.107")
val writeCollection = mongoClient.getDB("test").getCollection("data")

// Create
val msg = """
{ "name":"nathan","age":27,"profile":{"address":"none","ssn":null}}
"""
writeCollection.save( JObjectParser.parse(parse(msg)) )
writeCollection.save( JObjectParser.parse(parse("""{"tag":"foo"}""")) )

// Read
val readCollection  = mongoClient.getDatabase("test").getCollection("data")
readCollection.count
val doc = readCollection.find().first()
val cursor = readCollection.find().iterator()
try { while (cursor.hasNext()) {println(cursor.next().toJson())} } finally { cursor.close() }
doc.get("profile").asInstanceOf[org.bson.Document].toJson

}
