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

package de.heikoseeberger

import io.grpc.stub.{ CallStreamObserver, StreamObserver }

package object akkagrpc {

  /**
    * Implicitly converts a stream observer for responses to a more specific
    * `CallStreamObserver` simply by downcasting. This seems to be safe, as gRPC
    * seems to use the more specific `CallStreamObserver` when providing stream
    * observer for responses.
    *
    * @param responseObserver stream observer for responses provided by gRPC
    * @tparam A response type
    * @return stream observer for responses downcasted to `CallStreamObserver[A]`
    */
  implicit def toCallStreamObserver[A](
      responseObserver: StreamObserver[A]): CallStreamObserver[A] =
    responseObserver.asInstanceOf[CallStreamObserver[A]]
}
