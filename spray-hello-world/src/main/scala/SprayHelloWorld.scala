import akka.actor._
import akka.io.IO
import scala.concurrent.duration._
import spray.can.Http
import spray.http._
import spray.http.MediaTypes._
import spray.routing._
 
object SprayHelloWorld extends App {
  import java.net.InetAddress
  implicit val system = ActorSystem("spray-hello-world")
  val actorRef = system.actorOf(Props[MyActor], "handler")
  IO(Http) ! Http.Bind(actorRef, interface = InetAddress.getLocalHost.getHostAddress, port = 8080)
}

class MyActor extends Actor with HttpService {
  import context.dispatcher
  var count = 0
  def actorRefFactory = context
  def receive = runRoute(routes) orElse otherMessages
  val routes =
    path("hello") {
      get {
        respondWithMediaType(`application/json`) {
          complete { """{"msg":"hello world"} """ }
        }
      }
    } ~
    path("status") {
      get {
        respondWithMediaType(`application/json`) {
          complete { s""" {"count":$count, "uptime":${context.system.uptime}} """}
        }
      }
    }
  def otherMessages: Receive = {
    case "Tick" => count += 1
  }
  context.system.scheduler.schedule(0.seconds,2.seconds,self,"Tick")
}
