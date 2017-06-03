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

import akka.stream.QueueOfferResult.{
  Dropped,
  Enqueued,
  QueueClosed,
  Failure => OfferFailure
}
import akka.stream.scaladsl.{ Flow, Sink, Source, SourceQueueWithComplete }
import akka.stream.{ Materializer, OverflowStrategy }
import io.grpc.stub.{ CallStreamObserver, StreamObserver }
import scala.concurrent.ExecutionContext
import scala.util.{ Failure, Success }

/**
  * Bridge between server-side gRPC and Akka Streams. Executes back-pressure
  * onto the gRPC client.
  */
object RequestObserver {

  /**
    * Create a server-side gRPC stream observer for requests.
    *
    * @param handler transform requests into respons(es)
    * @param responseObserver stream observer for responses provided by gRPC
    * @param requestBufferSize buffer size for requests, 1 by default
    * @param ec implicit execution contetxt
    * @param mat implicit materializer
    * @tparam A request type
    * @tparam B response type
    * @return back-pressured server-side gRPC stream observer for requests
    */
  def apply[A, B](handler: Flow[A, B, Any],
                  responseObserver: CallStreamObserver[B],
                  requestBufferSize: Int = 1)(
      implicit ec: ExecutionContext,
      mat: Materializer): StreamObserver[A] = {

    responseObserver.disableAutoInboundFlowControl()
    responseObserver.request(requestBufferSize)

    val requestSource = {
      def toStreamObserver(requests: SourceQueueWithComplete[A]) = {
        def handleOnNext(value: A) =
          requests.offer(value).onComplete {
            case Success(Enqueued) =>
              responseObserver.request(1)
            case Success(Dropped) =>
              throw new IllegalStateException(
                "Dropped should be impossible!?!")
            case Success(QueueClosed) =>
              throw new IllegalStateException(
                s"Queue closed for offer $value!")
            case Success(OfferFailure(t)) =>
              throw new IllegalStateException(s"Failure for offer $value!", t)
            case Failure(t) =>
              throw new IllegalStateException(s"Failed to offer $value!", t)
          }
        new StreamObserver[A] {
          override def onError(t: Throwable) = requests.fail(t)
          override def onCompleted()         = requests.complete()
          override def onNext(a: A)          = handleOnNext(a)
        }
      }
      Source
        .queue[A](requestBufferSize, OverflowStrategy.backpressure)
        .mapMaterializedValue(toStreamObserver)
    }

    val responseSink =
      Sink.queue[B]().mapMaterializedValue { responses =>
        def pull(): Unit = {
          def onNextThenPull(b: B) = {
            responseObserver.onNext(b)
            pull()
          }
          responses.pull().onComplete {
            case Success(Some(b)) => onNextThenPull(b)
            case Success(None)    => responseObserver.onCompleted()
            case Failure(t)       => responseObserver.onError(t)
          }
        }
        pull()
      }

    requestSource.via(handler).to(responseSink).run()
  }
}
