package local

import akka.actor._

object Local extends App {
  implicit val system = ActorSystem("LocalSystem")
  val localActor = system.actorOf(Props[LocalActor], name = "LocalActor")
  localActor ! "START" 
}

class LocalActor extends Actor {

  val remote = context.actorSelection("akka.tcp://HelloRemoteSystem@172.31.15.148:2552/user/RemoteActor")
  var counter = 0

  def receive = {
    case "START" => remote ! "Hello from the LocalActor"
    case msg: String => 
      println(s"LocalActor received message: '$msg'")
      if (counter < 5) {
        sender ! "Hello back to you"
        counter += 1
      }
  }
}


