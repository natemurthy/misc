package examples
 
import java.net.URI
import java.util.concurrent.TimeUnit
import org.eclipse.jetty.websocket.client.ClientUpgradeRequest
import org.eclipse.jetty.websocket.client.WebSocketClient
 
/**
 * Example of a simple Echo Client.
 */
object EchoClient {
 
    def main(args: Array[String]) {
        val destUri = "ws://echo.websocket.org" 
        val client = new WebSocketClient()
        val socket = new EchoSocket()
        try {
            client.start()
            val echoUri = new URI(destUri)
            val request = new ClientUpgradeRequest()
            client.setDaemon(true)
            client.connect(socket, echoUri, request)
            println(s"Connecting to : $echoUri")
            println(s"Max idle timeout: ${client.getMaxIdleTimeout}")
            //socket.awaitClose(10, TimeUnit.SECONDS)
            socket.persistConnection()
        } catch {
          case t: Throwable => t.printStackTrace()
        } finally {
            try {
                client.stop();
            } catch {
                case e:Exception => e.printStackTrace()
            }
        }
    }
}

class Handler extends Runnable {

    val destUri = "ws://echo.websocket.org" 
    val client = new WebSocketClient()
    val socket = new EchoSocket()

    def run() {
        try {
            client.start()
            val echoUri = new URI(destUri)
            val request = new ClientUpgradeRequest()
            //client.setDaemon(true)
            client.connect(socket, echoUri, request)
            println(s"Connecting to: $echoUri")
            println(s"Max idle timeout: ${client.getMaxIdleTimeout} ms")
            //socket.awaitClose(10, TimeUnit.SECONDS)
            socket.persistConnection()
        } catch {
          case t: Throwable => t.printStackTrace()
        } finally {
            try {
                client.stop();
            } catch {
                case e:Exception => e.printStackTrace()
            }
        }
    }

}

// Example with executor service
object example {
    
import examples._, org.eclipse.jetty.websocket.client._, java.net.URI, java.util.concurrent._
val pool = Executors.newFixedThreadPool(4)
val handler = new Handler()
val s = handler.socket
pool.execute(handler)
s.sendMessage("wherefore art thou")
s.close
s.sendMessage("wherefore art thou")

}
