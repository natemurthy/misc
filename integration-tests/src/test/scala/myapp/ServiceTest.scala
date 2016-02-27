package myapp

import org.scalatest.FlatSpec

class ServiceSpec extends FlatSpec {
  "A Service" should "have a mapreduce method" in {
    val srv = new Service()
    assert( srv.mapreduce(List(1,2,3)) == 12 )
  }
}
