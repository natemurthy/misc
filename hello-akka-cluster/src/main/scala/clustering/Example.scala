package clustering

import akka.actor._
import akka.cluster._
import akka.cluster.ClusterEvent._
import akka.pattern.ask
import akka.util.Timeout
import java.util.concurrent.atomic.AtomicInteger
import language.postfixOps
import scala.concurrent.duration._

/**
 * Actor Messages 
 */
final case class TransformationJob(text: String)
final case class TransformationResult(text: String)
final case class JobFailed(reason: String, job: TransformationJob)
case object BackendRegistration

/**
 * Actor for frontend role 
 */
class TransformationFrontend extends Actor {

  var backends = IndexedSeq.empty[ActorRef]
  var jobCounter = 0

  def receive = {
    case job: TransformationJob if backends.isEmpty =>
      sender() ! JobFailed("Service unavailable, try again later", job)

    case job: TransformationJob =>
      jobCounter += 1
      backends(jobCounter % backends.size) forward job

    case BackendRegistration if !backends.contains(sender()) =>
      context watch sender()
      backends = backends :+ sender()

    case Terminated(a) =>
      backends = backends.filterNot(_ == a)
  }
}

/**
 * Companion object of frontend actor 
 */
object TransformationFrontend {
  def start() = {
    val system = ActorSystem("ClusterSystem"); val cluster = Cluster(system)
    val frontend = system.actorOf(Props[TransformationFrontend], name = "frontend")

    import java.net.InetAddress
    cluster.join(
      AddressFromURIString.parse(s"akka.tcp://ClusterSystem@${InetAddress.getLocalHost.getHostAddress.toString}:8080")
    )

    val counter = new AtomicInteger
    import system.dispatcher
    val delay = 5.seconds
    println(s"Initial delay of $delay")
    system.scheduler.schedule(delay, 2.seconds) {
      implicit val timeout = Timeout(5 seconds)
      (frontend ? TransformationJob("hello-" + counter.incrementAndGet())) onSuccess {
        case result => println(result)
      }
    }

  }
}

/**
 * Actor for backend role 
 */
class TransformationBackend extends Actor {

  val cluster = Cluster(context.system)

  override def preStart(): Unit = cluster.subscribe(self, classOf[MemberUp])
  override def postStop(): Unit = cluster.unsubscribe(self)

  def receive = {
    case TransformationJob(text) => sender() ! TransformationResult(text.toUpperCase)
    case state: CurrentClusterState =>
      state.members.filter(_.status == MemberStatus.Up) foreach register
    case MemberUp(m) => register(m)
  }

  def register(member: Member): Unit =
    if (member.hasRole("frontend"))
      context.actorSelection(RootActorPath(member.address) / "user" / "frontend") ! BackendRegistration
}

/**
 * Companion object of backend actor 
 */
object TransformationBackend {
  def start(addr:String) = {
    val system = ActorSystem("ClusterSystem"); val cluster = Cluster(system)
    system.actorOf(Props[TransformationBackend], name = "backend")
    cluster.join(AddressFromURIString.parse(s"akka.tcp://ClusterSystem@$addr:8080"))
  }
}

/**
 * Worker actor for backend role
 */
class Worker extends Actor {

  val cluster = Cluster(context.system)

  override def preStart(): Unit = cluster.subscribe(self, classOf[MemberUp])
  override def postStop(): Unit = cluster.unsubscribe(self)

  def receive = {
    case TransformationJob(text) =>
      println(s"from $sender: \ntransformed $text to ${text.toUpperCase}")
    case state: CurrentClusterState =>
      state.members.filter(_.status == MemberStatus.Up) foreach register
    case MemberUp(m) => register(m)
  }

  def register(member: Member): Unit =
    if (member.hasRole("frontend"))
      context.actorSelection(RootActorPath(member.address) / "user" / "master") ! BackendRegistration
}

/**
 * Master actor for frontend role
 */
class Master extends Actor {

  var backends = IndexedSeq.empty[ActorRef]
  var jobCounter = 0

  def receive = {
    case job: TransformationJob if backends.isEmpty =>
      sender() ! JobFailed("Service unavailable, try again later", job)
    case job: TransformationJob =>
      jobCounter += 1
      backends(jobCounter % backends.size) forward job
    case BackendRegistration if !backends.contains(sender()) =>
      context watch sender()
      backends = backends :+ sender()
    case Terminated(a) =>
      backends = backends.filterNot(_ == a)
  }
}
