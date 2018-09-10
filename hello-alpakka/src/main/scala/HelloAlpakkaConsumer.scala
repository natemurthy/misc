import akka.actor.ActorSystem
import akka.kafka.{ConsumerSettings, Subscriptions}
import akka.kafka.scaladsl.Consumer
import akka.stream.scaladsl.{Keep, Sink}
import akka.stream.{ActorMaterializer, Materializer}
import com.typesafe.config.{ConfigFactory,ConfigValueFactory}
import org.apache.kafka.common.serialization.StringDeserializer
import org.slf4j.LoggerFactory

import scala.concurrent.ExecutionContextExecutor
import scala.util.{Failure, Success}

/**
  * Consumer example borrowed from
  * https://gist.github.com/davideicardi/ff914afe01cd8db97bae16a533d21fc8
  */
object HelloAlpakkaConsumer extends App {

  private[this] val log = LoggerFactory.getLogger(getClass.getName.stripSuffix("$"))
  private[this] val config = ConfigFactory.load()
  private[this] val topic = config.getString("akka.kafka.consumer.kafka-clients.topic")

  log.info("Hello from Alpakka")

  implicit val system: ActorSystem = ActorSystem("hello-alpakka")
  implicit val ec: ExecutionContextExecutor = system.dispatcher
  implicit val materializer: Materializer = ActorMaterializer()

  val settings = ConsumerSettings(system, new StringDeserializer, new StringDeserializer)

  val consumer = Consumer
    .plainSource(settings, Subscriptions.topics(topic))
    .toMat(Sink.foreach(r => println(r.value)))(Keep.both)
    .mapMaterializedValue(Consumer.DrainingControl.apply)
    .run()

  sys.addShutdownHook({
    log.info("Shutdown requested...")

    val done = consumer.shutdown()

    done
      .onComplete {
        case Success(_) => log.info("Done"); system.terminate()
        case Failure(err) => log.error(err.toString); system.terminate()
      }
  })

}
