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
        val destUri = "ws://gw.solarcity.com:2012/test-1234"
        val client = new WebSocketClient();
        val socket = new EchoSocket();
        try {
            client.start();
            val echoUri = new URI(destUri);
            val request = new ClientUpgradeRequest();
            client.connect(socket, echoUri, request);
            println("Connecting to : %s%n", echoUri);
            socket.awaitClose(5, TimeUnit.SECONDS);
        } catch {
          case t: Throwable => t.printStackTrace();
        } finally {
            try {
                client.stop();
            } catch {
                case e:Exception => e.printStackTrace();
            }
        }
    }
}
