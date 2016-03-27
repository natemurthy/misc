package myapp.integration

import myapp._
import myapp.integration.setup.IntegrationFunSuite

class ServiceIntegrationTest extends IntegrationFunSuite {

  lazy val srv = new ServiceImpl{ host = sys.env("CONTAINER_HOST") }

  test("write to database") {
    srv.writeToDb("Damian Lillard")
  }

  test("publish to message broker") {
    srv.publish("kumusta ka na")
  }

}
