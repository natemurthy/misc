import akka.actor.ActorSystem
import akka.kafka.{ConsumerSettings, Subscriptions}
import akka.kafka.scaladsl.Consumer
import akka.stream.scaladsl.{Keep, Sink}
import akka.stream.{ActorMaterializer, Materializer}
import org.apache.kafka.common.serialization.StringDeserializer

import scala.concurrent.ExecutionContextExecutor
import scala.util.{Failure, Success}

/**
  * Consumer example borrowed from
  * https://gist.github.com/davideicardi/ff914afe01cd8db97bae16a533d21fc8
  */
object HelloAlpakkaConsumer extends App {

  println("Hello from Alpakka")

  implicit val system: ActorSystem = ActorSystem("hello-alpakka")
  implicit val materializer: Materializer = ActorMaterializer()

  val consumerSettings =
    ConsumerSettings(system, new StringDeserializer, new StringDeserializer)
      .withBootstrapServers(args.head)

  val consumer = Consumer
    .plainSource(consumerSettings, Subscriptions.topics("streams-plaintext-input"))
    .toMat(Sink.foreach(r => println(r.value)))(Keep.both)
    .mapMaterializedValue(Consumer.DrainingControl.apply)
    .run()

  sys.addShutdownHook({
    println("Shutdown requested...")

    val done = consumer.shutdown()

    implicit val ec: ExecutionContextExecutor = system.dispatcher
    done
      .onComplete {
        case Success(_) => println("Done"); system.terminate()
        case Failure(err) => println(err.toString); system.terminate()
      }
  })

}
