/*
 * Copyright 2017 Heiko Seeberger
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package de.heikoseeberger.akkagrpc.example

import io.grpc.ManagedChannelBuilder
import io.grpc.stub.StreamObserver
import java.util.concurrent.TimeUnit

object ExampleClientApp {

  def main(args: Array[String]): Unit = {
    val channel =
      ManagedChannelBuilder
        .forAddress("localhost", 8000)
        .usePlaintext(true)
        .build
    val client = ExampleServiceGrpc.stub(channel)

    val responseObserver =
      new StreamObserver[ExampleResponse] {

        override def onError(t: Throwable) = println(t)

        override def onCompleted() = {
          println("Completed")
          channel.shutdown()
        }

        override def onNext(response: ExampleResponse) =
          println(s"Received response with message = ${response.message}")
      }
    val requestObserver = client.exampleCall(responseObserver)

    for (n <- 1 to 3)
      requestObserver.onNext(ExampleRequest(s"request-$n"))

    requestObserver.onNext(ExampleRequest("last-message"))

    requestObserver.onCompleted()

    channel.awaitTermination(7, TimeUnit.SECONDS)
  }
}
