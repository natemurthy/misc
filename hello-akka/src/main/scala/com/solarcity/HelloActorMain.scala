package com.solarcity

import akka.actor.{Actor,ActorSystem,Props}
import scala.concurrent.duration._
import scala.concurrent.ExecutionContext.Implicits.global
import scala.util.Random

case class Message(msg: String)

class HelloActor extends Actor {
  var internalState: String = _
  def receive = {
    case Message(m) => println(m); internalState = m
  }
}

object HelloActorMain extends App {

  val msgList = List("hello world", "how are you?", "what's your name", "good to know", "ok great", "thanks goodbye")
  val rand = new Random()

  val system = ActorSystem()
  val actor = system.actorOf(Props[HelloActor])
  system.scheduler.schedule(initialDelay=0.seconds, interval=2.seconds) {
    actor ! Message(msgList(rand.nextInt(msgList.length)))
  }
}
