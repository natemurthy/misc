package controllers

import org.scalatest.Matchers
import play.api.test._
import play.api.test.Helpers._
import test.mixins.FlatSpecWithFakeApp

class ServiceTwoApiSpec extends FlatSpecWithFakeApp with Matchers {

  "Service Two API" should "have a /ping endpoint" in {
     val result = route(FakeRequest(GET, "/ping")).get
     status(result) shouldBe OK
   }

}
