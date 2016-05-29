object Main extends App {
  import org.iq80.leveldb._, org.fusesource.leveldbjni.JniDBFactory._, java.io._
  val options = new Options(); options.createIfMissing(true); val db = factory.open(new File("example"), options)
}
