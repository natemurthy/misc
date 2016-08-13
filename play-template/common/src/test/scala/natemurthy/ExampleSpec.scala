package natemurthy

import org.scalatest.{FlatSpec,Matchers}

class ExampleSpec extends FlatSpec with Matchers {

  val example = new Example
  "Example is a class that" should "have a testable foo() method" in {
     example.foo should equal("hello world")
   }

}

