#!/usr/bin/env amm
import $ivy.`org.apache.curator:curator-recipes:2.11.0`

import java.util.concurrent.Executors
import org.apache.zookeeper.KeeperException.{ NoNodeException, NodeExistsException }
import org.apache.curator.framework.CuratorFrameworkFactory
import org.apache.curator.retry.ExponentialBackoffRetry
import org.apache.curator.framework.recipes.leader.LeaderLatch
import org.apache.curator.framework.recipes.leader.LeaderLatchListener
import scala.util.Random

val connStr = "127.0.0.1:2181"
val retryPolicy = new ExponentialBackoffRetry(1000, 3)
val curatorBuilder = CuratorFrameworkFactory.builder().connectString(connStr).retryPolicy(retryPolicy) 

val client = curatorBuilder.build()
client.start()
client.blockUntilConnected()
println("connected")

val myId = s"id-${Math.abs(Random.nextInt)}"
val serialExecutor = Executors.newSingleThreadExecutor()
val listener = new LeaderLatchListener {
  private var leading = false
  override final def notLeader(): Unit =
    if (leading) {
      println("!!! CRASH CRASH CRASH !!!")
    }

  override final def isLeader(): Unit = {
    if (!leading) {
      leading = true
      println("we're the leader; trigger transition accordingly.")
    }
  }
}

val latch = new LeaderLatch(client, "/test", myId)
latch.addListener(listener, serialExecutor)
latch.start()

println(s"myId = ${myId}")
new Thread { override def run() = Thread.sleep(Long.MaxValue) }.start
