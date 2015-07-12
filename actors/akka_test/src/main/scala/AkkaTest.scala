import akka.actor.{Actor, ActorSystem, PoisonPill, Props}

case class Message(i: Int)

class Counter(limit: Int)  extends Actor {
  var counter = 0
  def receive = {
    case Message(i) => counter = i; if (counter == limit) self ! PoisonPill
  }
}
 
object AkkaTest extends AkkaTestLike {
  def main(args: Array[String]) {
	val N = 1000000
    ref = system.actorOf(Props(new Counter(N)), name = "Counter")
    withCleanShutdown()
    val start = System.nanoTime
    for (i <- (1 to N)) { ref ! Message(i) }
    val end = System.nanoTime
    println(s"Time to process $N messages: ${(end-start)/1.0e9} s")
  }
}
