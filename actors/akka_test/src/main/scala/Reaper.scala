import akka.actor.{Actor, ActorRef, ActorSystem, Props, Terminated}
 
case class Watch(ref: ActorRef)
 
class Reaper extends Actor {
  def gracefullyShutdown(): Unit = context.system.shutdown()
 
  final def receive = {
    case Watch(ref) => context.watch(ref)
    case Terminated(ref) => gracefullyShutdown()
  }
}

trait AkkaTestLike {
  val system = ActorSystem("CounterSystem")
  val reaper = system.actorOf(Props[Reaper], name="Reaper")
  var ref: ActorRef = _
  def withCleanShutdown(): Unit = reaper ! Watch(ref)
}
