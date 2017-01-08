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

val res2 = Await.result(znode.exists())
println(s"znode.exists: $res2")

val res3 = Await.result(znode.getData())
println(s"znode.getData: ${new String(res3.bytes)}")

val res4 = Await.result(znode.setData("more junk".getBytes,version=1))
println(s"znode.setData: $res4")

val res5 = Await.result(znode.getData())
println(s"znode.getData: ${new String(res5.bytes)}")

