object example {

// play ws example
import play.api.libs.ws.ning.NingWSClient
import com.ning.http.client.AsyncHttpClientConfig.Builder
import concurrent.ExecutionContext.Implicits.global
val client1 = new NingWSClient(new Builder().build())
client1.url("http://54.201.45.53:5000/api/rest/status").get().map(r => println(r.body))

// jersey / jax-rs example
import javax.ws.rs.client._
ClientBuilder.newClient().target("http://54.201.45.53:5000").path("api/rest/status").request().get(classOf[String])

}


