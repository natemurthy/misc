package com.bigcommerce.fortune

import akka.actor.ActorSystem

/**
  * Created by zack.angelo on 5/30/17.
  */
trait Config {
  val (interface,port) = ("127.0.0.1", 9000)

  implicit val actorSystem = ActorSystem("fortune-cookie")
}
