package myapp

import com.orientechnologies.orient.core.db.ODatabaseRecordThreadLocal
import com.thenewmotion.akka.rabbitmq._
import com.tinkerpop.blueprints._
import com.tinkerpop.blueprints.impls.orient._

trait Service {
  def mapreduce(xs: List[Int]): Int

  def writeToDb(name:String): Unit

  def publish(msg:String): Unit
}

class ServiceImpl extends Service {

  var host: String = _

  def mapreduce(xs: List[Int]): Int = xs.map(_*2).reduce(_+_)

  def writeToDb(name: String): Unit = {
    if (ODatabaseRecordThreadLocal.INSTANCE != null) {
      val graph = new OrientGraph(s"remote:$host/mydb")
      val v = graph.addVertex("class:MyRecord", Nil: _*)
      val uuid = java.util.UUID.randomUUID.toString
      v.setProperty("name", name)
      v.setProperty("uuid", uuid)
      println(s"Writing to DB: $v")
      graph.commit()
    }
  }

  def publish(msg: String): Unit = {
    val factory = new ConnectionFactory()
    factory.setHost(host)
    factory.setUsername("guest")
    factory.setPassword("guest")
    val connection: Connection = factory.newConnection()
    val channel: Channel = connection.createChannel()
    val queue = channel.queueDeclare().getQueue
    channel.queueBind(queue, "amq.topic", "routingKey")
    channel.basicPublish("amq.topic", queue, null, msg.getBytes)
    println(s"published: $msg")
    channel.close()
    connection.close()
  }

}
