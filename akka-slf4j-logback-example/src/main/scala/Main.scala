import com.typesafe.config.ConfigFactory
import akka.actor._
import concurrent.duration._

object Main extends App {

  lazy val log = org.slf4j.LoggerFactory.getLogger(this.getClass.getName.replace("$",""))

  val config = ConfigFactory.load()
  val system = ActorSystem("app", config)
  system.actorOf(Props[MyActor],"my-actor")


  import system.dispatcher
  system.scheduler.schedule(0.seconds,4.seconds) {
    log.debug(Console.MAGENTA+"some debug level logging stuff"+Console.RESET)
    log.info(Console.CYAN+"some info level logging stuff here"+Console.RESET)
    log.warn(Console.YELLOW+"some warning messages"+Console.RESET)
    log.error(Console.RED+"danger danger will robinson"+Console.RESET)
  }

  system.awaitTermination()

}

class MyActor extends Actor with ActorLogging {

  import context._

  override def preStart() = {
    context.system.scheduler.schedule(0.seconds,3.seconds,self,"msg")
  }

  def receive = {
    case _ => {
      log.debug("actor debug msg")
      log.info("info level stuff")
      log.warning("uh oh gotta bad feeling")
      log.error("yep this sucks")
    }
  }
}
