package test

import org.scalatest._
import play.api.Play
import play.api.test.FakeApplication

package object mixins {

  trait FlatSpecWithFakeApp extends FlatSpec with BeforeAndAfterAll {
    implicit val fakeApp: FakeApplication = new FakeApplication()
    override protected def beforeAll(configMap: ConfigMap): Unit = Play.start(fakeApp)
    override protected def  afterAll(configMap: ConfigMap): Unit = Play.stop(fakeApp)
  }

}

