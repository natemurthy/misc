import java.util.Collection
import java.util.concurrent.{Callable, Executors, ExecutorService}
import scala.collection.JavaConverters._

object JavaPool {

  def factorize(number: Int, list: List[Int] = List()): List[Int] = {
    for(n <- 2 to number if (number % n == 0)) {
      return factorize(number / n, list :+ n)
    }
    list
  }
  
  class Factorizer(n: Int) extends Callable[Unit] {
    def call() { factorize(n) }
  }
  
  def createTasks(n: Int) = (100 until n).map(new Factorizer(_))

  def main(args: Array[String]) {
    val cpuCount = Runtime.getRuntime().availableProcessors()
    val pool = Executors.newFixedThreadPool(cpuCount)
    val tasks = createTasks(args(0).toInt).asJava
    val start = System.nanoTime; pool.invokeAll(tasks); val end = System.nanoTime;
    pool.shutdown()
    println((end-start)/1e9)
  }

}
