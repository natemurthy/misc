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
class EchoSocket {
 
    private val _closeLatch = new CountDownLatch(1)
    private var _session: Session = _
 
    @OnWebSocketClose
    def onClose(statusCode:Int, reason:String) = {
        println(s"Connection closed: $statusCode - $reason")
        _session = null
        _closeLatch.countDown()
    }
 
    @OnWebSocketConnect
    def onConnect(session:Session) {
        println(s"Connection established: ${session}")
        _session = session
        try {
            var fut: Future[Void] = null
            fut = session.getRemote().sendStringByFuture("Hello")
            fut.get(2, TimeUnit.SECONDS)
            fut = session.getRemote().sendStringByFuture("Thanks for the conversation.")
            fut.get(2, TimeUnit.SECONDS)
            //session.close(StatusCode.NORMAL, "I'm done");
        } catch {
           case t:Throwable => t.printStackTrace();
        }
    }
 
    @OnWebSocketMessage
    def onMessage(msg:String) {
        println(s"Got msg: $msg")
    }

    @throws[InterruptedException]
    def awaitClose(duration:Int, unit:TimeUnit): Boolean = {
        return _closeLatch.await(duration, unit)
    }

    private[this] def useSessionFor(func: Session => Any) {
        Option(_session) match {
            case Some(s) => func(s)
            case None    => println("Session no longer available")
        }
    }

    @throws[InterruptedException]
    def persistConnection() = _closeLatch.await()

    def sendMessage(msg:String) = useSessionFor((s:Session) => s.getRemote.sendStringByFuture(msg))

    def close() = useSessionFor((s:Session) => s.close(StatusCode.NORMAL, "I'm done"))

}
