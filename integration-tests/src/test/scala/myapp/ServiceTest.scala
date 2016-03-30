package myapp

import org.scalatest.FlatSpec

class ServiceTest extends FlatSpec {
  "A Service" should "have a mapreduce method" in {
    val srv = new ServiceImpl()
    assert( srv.mapreduce(List(1,2,3)) == 12 )
  }
}
