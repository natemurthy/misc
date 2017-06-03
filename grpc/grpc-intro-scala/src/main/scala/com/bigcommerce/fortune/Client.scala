package com.bigcommerce.fortune

import com.bigcommerce.fortune.Fortune.{FortuneCookieGrpc, FortunePerSecReq, FortunePerSecResp, NextFortuneReq}
import io.grpc.netty.NettyChannelBuilder
import io.grpc.stub.StreamObserver

/**
  * Created by zack.angelo on 5/30/17.
  */
object Client
  extends App
  with Config {

  val channel = NettyChannelBuilder
    .forAddress(interface, port)
    .usePlaintext(true)
    .build()

//  val client = FortuneCookieGrpc.blockingStub(channel)
//  println(client.nextFortunes(NextFortuneReq(2)))

  val client = FortuneCookieGrpc.stub(channel)

  client.fortunePerSecond(FortunePerSecReq(), new StreamObserver[FortunePerSecResp] {
    override def onError(t: Throwable): Unit = t.printStackTrace()

    override def onCompleted(): Unit =
      println("stream completed")

    override def onNext(value: FortunePerSecResp): Unit = {
      println(s"Fortune received! ${value.fortune}")
    }
  })

  Thread.sleep(6000)
}
