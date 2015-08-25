import com.orientechnologies.orient.client.remote.OServerAdmin
import com.orientechnologies.orient.core.record.impl.ODocument
import org.scalatest.FlatSpec

import com.orientechnologies.orient.core.id.ORecordId
import com.orientechnologies.orient.core.sql.query.OSQLSynchQuery
import scala.collection.JavaConversions._
import com.orientechnologies.orient.`object`.db.OObjectDatabaseTx
import javax.persistence.{Version, Id}

class test extends FlatSpec {

  class User {
    @Id var id: String = _
    var name: String = _
    var addresses: java.util.List[Address] = new java.util.ArrayList()
    @Version var version: String = _

    override def toString = "User: " + this.id + ", name: " + this.name + ", addresses: " + this.addresses
  }

  class Address {
    var city: String = _
    var street: String = _

    override def toString = "Address: " + this.city + ", " + this.street
  }

  class Question {
    @Id var id: String = _
    var title: String = _
    var user: User = _
    @Version var version: String = _

    override def toString = "Question: " + this.id + ", title: " + this.title + ", belongs: " + user.name
  }

//  implicit def dbWrapper(db: OObjectDatabaseTx) = new {
//    def queryBySql[T](sql: String, params: AnyRef*): List[T] = {
//      val params4java = params.toArray
//      val results: java.util.List[T] = db.query(new OSQLSynchQuery[T](sql), params4java: _*)
//      results.asScala.toList
//    }
//  }

  ignore should "write to orient db" in {
    val uri = "remote:localhost/documents"
    val db = new OObjectDatabaseTx(uri)
    db.open("root","password")

    db.getEntityManager.registerEntityClass(classOf[User])
    db.getEntityManager.registerEntityClass(classOf[Address])
    db.getEntityManager.registerEntityClass(classOf[Question])

    val user: User = new User
    user.name = "aaa"
    db.save(user)

    var address1 = new Address
    address1.city = "NY"
    address1.street = "road1"
    var address2 = new Address
    address2.city = "ST"
    address2.street = "road2"

    user.addresses += address1
    user.addresses += address2
    db.save(user)

    val q1 = new Question
    q1.title = "How to use orientdb in scala?"
    q1.user = user
    db.save(q1)

    val q2 = new Question
    q2.title = "Show me a demo"
    q2.user = user
    db.save(q2)

    db.close()

  }

  it should "read from orient db" in {
    import scala.collection.JavaConversions._
    val uri = "remote:localhost/documents"
    val db = new OObjectDatabaseTx(uri)
    db.open("root","password")

    db.getEntityManager.registerEntityClass(classOf[User])
    db.getEntityManager.registerEntityClass(classOf[Address])
    db.getEntityManager.registerEntityClass(classOf[Question])

    val users = db.query(new OSQLSynchQuery[ODocument]("select from User"), Nil: _*).asInstanceOf[java.util.ArrayList[ODocument]]
    users foreach println
    db.close()
  }

  ignore should "drop db" in {
    val uri = "remote:localhost/documents"
    val db = new OServerAdmin(uri).connect("root","password")
    db.dropDatabase("remote")
  }

}
