package com.solarcity

import akka.actor.ActorSystem
import akka.testkit.{ImplicitSender, TestActorRef, TestKit}
import org.scalatest.{Matchers, FlatSpecLike}

class HelloActorTest
  extends TestKit(ActorSystem()) 
  with Matchers
  with FlatSpecLike {

  val actorRef = TestActorRef(new HelloActor())
  
  "HelloActor's internal state" should "change whenever it receives a Message" in {
    val msg = "hello"
    actorRef ! Message(msg)
    actorRef.underlyingActor.internalState shouldBe msg
  }
}

