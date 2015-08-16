import akka.actor._
import akka.io.IO
import spray.can.Http
import spray.http.MediaTypes._
import spray.routing._
 
object SprayHelloWorld extends App {
  implicit val system = ActorSystem("spray-hello-world")
  val actorRef = system.actorOf(Props[MyActor], "my-actor")
  IO(Http) ! Http.Bind(actorRef, interface = "localhost", port = 8080)
}

class MyActor extends Actor with MyService {
  def actorRefFactory = context
  def receive = runRoute(routes)
}

trait MyService extends HttpService {
  val routes =
    path("status") {
      get {
        respondWithMediaType(`application/json`) {
          _.complete { """{"msg":"hello world"} """ }
        }
      }
    } 
}

