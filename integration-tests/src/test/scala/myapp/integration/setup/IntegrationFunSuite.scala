
package myapp.integration.setup

import org.scalatest.{FunSuite, Tag}

/**
  * All integration tests should be marked with this tag.
  * Integration tests need a special set up and can take a long time.
  * So it is not desirable, that these kind of tests run every time all the unit tests run.
  */
object IntegrationTag extends Tag("integration")

/**
  * Convenience trait, which will mark all test cases as integration tests.
  */
trait IntegrationFunSuite extends FunSuite {
  override protected def test(testName: String, testTags: Tag*)(testFun: => Unit): Unit = {
    super.test(testName, IntegrationTag +: testTags: _*)(testFun)
  }
}
