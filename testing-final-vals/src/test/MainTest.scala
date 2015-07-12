import org.scalatest.{FlatSpec,Matchers}

class MainTest extends FlatSpec with Matchers {
  it should "have a name" in {
    Main1.NAME shouldBe "foo"
  }
  it should "also have a name" in {
  	Main2.NAME shouldBe "foo"
  }
}
