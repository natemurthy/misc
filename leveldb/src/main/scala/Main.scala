object Main extends App {
  import org.iq80.leveldb._, org.fusesource.leveldbjni.JniDBFactory._, java.io._
  val options = new Options(); options.createIfMissing(true); val db = factory.open(new File("example"), options)
  try {
    db.put(bytes("Tampa"), bytes("rocks"))
    val a = asString(db.get(bytes("Tampa")))
    println(a)
    db.delete(bytes("Tampa"))
    val b = asString(db.get(bytes("Tampa")))
    println(b)
    println(db.getProperty("leveldb.stats"))
  } finally {
    db.close()
  }
}
