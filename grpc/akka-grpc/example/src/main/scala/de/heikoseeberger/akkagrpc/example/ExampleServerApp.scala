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

package de.heikoseeberger.akkagrpc
package example

import akka.actor.ActorSystem
import akka.stream.scaladsl.Flow
import akka.stream.{ ActorMaterializer, ThrottleMode }
import de.heikoseeberger.akkagrpc.example.ExampleServiceGrpc.bindService
import io.grpc.ServerBuilder
import io.grpc.stub.StreamObserver
import scala.concurrent.Await
import scala.concurrent.duration.{ Duration, DurationInt }

object ExampleServerApp {

  private final class ExampleService(implicit system: ActorSystem)
      extends ExampleServiceGrpc.ExampleService {
    import system.dispatcher

    private implicit val mat = ActorMaterializer()

    override def exampleCall(
        responseObserver: StreamObserver[ExampleResponse]) = {
//      val handler =
//        Flow[ExampleRequest]
//          .throttle(1, 1.second, 1, ThrottleMode.shaping)
//          .map(request => ExampleResponse(request.message.toUpperCase))
      val handler =
        Flow[ExampleRequest]
          .throttle(1, 1.second, 1, ThrottleMode.shaping)
          .map { req =>
            println(req); req
          }
          .fold(Vector.empty[String])(_ :+ _.message.toUpperCase)
          .map(messages => ExampleResponse(messages.mkString("/")))
      RequestObserver(handler, responseObserver)
    }
  }

  def main(args: Array[String]): Unit = {
    implicit val system = ActorSystem()
    ServerBuilder
      .forPort(8000)
      .addService(bindService(new ExampleService, system.dispatcher))
      .build()
      .start()
    println("Starting server on port 8000")
    Await.ready(system.whenTerminated, Duration.Inf)
  }
}
