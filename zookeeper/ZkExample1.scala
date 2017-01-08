#!/usr/bin/env amm
import $ivy.`com.twitter::util-zk:6.34.0`
 
import java.util.concurrent.TimeUnit
import com.twitter.util.{ Future => TWFuture, Duration, JavaTimer, Await }
import com.twitter.zk.{NativeConnector, StateEvent, ZkClient, ZNode}
import org.apache.zookeeper.ZooDefs
import scala.collection.JavaConverters._, scala.concurrent.{Future,Promise}

val zkHosts = "localhost:2181"; val authInfo = None
val sessionTimeoutTw = Duration(5, TimeUnit.SECONDS)
val connector = NativeConnector(zkHosts, None, sessionTimeoutTw, new JavaTimer(isDaemon = true), authInfo)
val zkClient = ZkClient(connector).withAcl(ZooDefs.Ids.OPEN_ACL_UNSAFE.asScala.toSeq)
val znode = ZNode(zkClient, "/zk_test")

val printSesssionEvent: PartialFunction[StateEvent,Unit] = {
  case e: StateEvent => println(s"state change event: type ${e.eventType}, state ${e.state}") 
}
zkClient.onSessionEvent(printSesssionEvent)

val res1 = Await.result(znode.create("data".getBytes))
println(s"znode.create: $res1")

val res2 = Await.result(znode.exists())
println(s"znode.exists: $res2")

val res3 = Await.result(znode.getData())
println(s"znode.getData: ${new String(res3.bytes)}")

val res4 = Await.result(znode.setData("junk".getBytes,version=0))
println(s"znode.setData: $res4")

val res5 = Await.result(znode.getData())
println(s"znode.getData: ${new String(res5.bytes)}")

def watchAndGetData = for {
  watch <- znode.getData.watch()
      _ <- watch.update // waits until WatchedEvent occurs
    res <- znode.getData()
} yield res

println("Waiting for WatchedEvent...")
val res6 = Await.result(watchAndGetData)
println(s"watchAndGetData: $res6")

val res7 = Await.result(znode.delete(version=2))
println(s"znode.delete: $res7")

try {
  val res8 = Await.result(znode.exists())
  println(s"znode.exists: $res8")
} catch {
  case ex: Exception => println(ex.getMessage)
}

implicit class Twitter2Scala[T](val twitterF: TWFuture[T]) extends AnyVal {
  def asScala: Future[T] = {
    val promise = Promise[T]()
    twitterF.onSuccess(promise.success(_))
    twitterF.onFailure(promise.failure(_))
    promise.future
  }
}
