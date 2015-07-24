import java.sql._
import com.wda.sdbc.SqlServer._
import resource._

object Example extends App {
  val connectionUrl = "jdbc:jtds:sqlserver://server;" +
                      "user=USER;" +
                      "password=PASSWD;" +
                      "applicationName=MyApp" ;
  val conn = DriverManager.getConnection(connectionUrl)
  val results = conn.iterator("SELECT TOP 10 * FROM DB..TABLE").map(
        (row: Row) =>
            row[Int]("key") -> row[String]("value")
    ).toMap
  results foreach println

}
