package examples;
 
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import org.eclipse.jetty.websocket.api.Session;
import org.eclipse.jetty.websocket.api.StatusCode;
import org.eclipse.jetty.websocket.api.annotations.OnWebSocketClose;
import org.eclipse.jetty.websocket.api.annotations.OnWebSocketConnect;
import org.eclipse.jetty.websocket.api.annotations.OnWebSocketMessage;
import org.eclipse.jetty.websocket.api.annotations.WebSocket;
 
/**
 * Basic Echo Client Socket
 */
@WebSocket(maxTextMessageSize = 64 * 1024)
class EchoSocket(var closeLatch:CountDownLatch = new CountDownLatch(1)) {
 
    private var session: Session = _;
 
    @throws[InterruptedException]
    def awaitClose(duration:Int, unit:TimeUnit): Boolean = {
        return closeLatch.await(duration, unit);
    }
 
    @OnWebSocketClose
    def onClose(statusCode:Int, reason:String) = {
        println(s"Connection closed: $statusCode - $reason");
        session = null;
        closeLatch.countDown();
    }
 
    @OnWebSocketConnect
    def onConnect(_session:Session) {
        println(s"Got connect: ${_session}");
        session = _session;
        try {
            var fut: Future[Void] = null
            fut = session.getRemote().sendStringByFuture("Hello");
            fut.get(2, TimeUnit.SECONDS);
            fut = session.getRemote().sendStringByFuture("Thanks for the conversation.");
            fut.get(2, TimeUnit.SECONDS);
            session.close(StatusCode.NORMAL, "I'm done");
        } catch {
           case t:Throwable => t.printStackTrace();
        }
    }
 
    @OnWebSocketMessage
    def onMessage(msg:String) {
        println(s"Got msg: $msg");
    }
}
