package com.bigcommerce.fortune

import java.net.InetSocketAddress

import akka.actor.{Actor, PoisonPill, Props}
import io.grpc.netty.NettyServerBuilder

import scala.io.Source
import scala.util.Random
import com.bigcommerce.fortune.Fortune._
import io.grpc.stub.StreamObserver

import scala.concurrent.Future

/**
  * Created by zack.angelo on 5/30/17.
  */
object Server
  extends App
  with Config {

  def parseFortuneFile(fortuneFile: java.io.InputStream,
                       delimiter: String): Array[String] =
    Source
      .fromInputStream(fortuneFile, "utf-8").getLines.mkString("\n")
      .split(delimiter)
      .map {
        _.replace('\n', ' ').trim
      }

  // load fortunes from resoruces
  val FORTUNES: Array[String] = parseFortuneFile(
    getClass.getResourceAsStream("pg_fortunes.txt"),
    "%")

  // pull a random fortune
  def randomFortune = FORTUNES(Random.nextInt(FORTUNES.length))

  // pull many random fortunes
  def randomFortuneSeq(n: Int): Seq[String] =
    for { _ <- 0 to n } yield randomFortune

  //probably don't want this in production
  implicit val EC =
    scala.concurrent.ExecutionContext.Implicits.global

  val Impl = new FortuneCookieGrpc.FortuneCookie {
    override def nextFortunes(request: NextFortuneReq): Future[NextFortuneResp] = {
      Future.successful(NextFortuneResp(randomFortuneSeq(request.numFortunes)))
    }

    override def fortunePerSecond(request: FortunePerSecReq,
                                  responseObserver: StreamObserver[FortunePerSecResp]): Unit = {

      import scala.concurrent.duration._

      val props = Props(new Actor {

        val repeat = context.system.scheduler.schedule(0 seconds, 1 second, self, "send")

        context.system.scheduler.scheduleOnce(5 seconds, self, PoisonPill)

        override def receive: Receive = {
          case "send" =>
            try {
              responseObserver.onNext(FortunePerSecResp(randomFortune))
            } catch {
              case _ : Throwable =>
                println("stream died")
                self ! PoisonPill
            }
        }

        override def postStop(): Unit = {
          super.postStop()
          responseObserver.onCompleted()
        }
      })

      actorSystem.actorOf(props)
    }
  }

  val server = NettyServerBuilder
    .forAddress(new InetSocketAddress(interface, port))
    .addService(FortuneCookieGrpc.bindService(Impl, EC))
    .build()

  server.start()

  println(s"Server started on $interface:$port")

  server.awaitTermination()
}
