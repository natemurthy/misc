package myapp

object ServiceMain extends App {
  val srv = new Service()
  println(s"Let's do a mapreduce: ${srv.mapreduce(List(1,2,3))}")
}

class Service {
  def mapreduce(xs: List[Int]): Int = xs.map(_*2).reduce(_+_)

  def writeToDb: Unit = ???

  def readFromDb: Unit = ???

  def publish: Unit = ???

  def subscribe: Unit = ???
}
