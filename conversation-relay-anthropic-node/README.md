# twilio + claude integration (via ngrok)

https://www.twilio.com/en-us/blog/integrate-anthropic-twilio-voice-using-conversationrelay

Start ngrok with `ngrok http 8080` 

> [!NOTE]  
> The URL will be different on each shell command invocation of `ngrok`. Both the phone number webhook configuration
> and env var need to updated each time.

And run then the integration server with
```
NGROK_URL="ffff-NN-NN-N-NN.ngrok-free.app" node server.js
```

Sample log of demo run:
```
[dotenv@17.3.1] injecting env (0) from .env -- tip: 🛠️  run anywhere with `dotenvx run -- yourcommand`
Server running at http://localhost:8080 and wss://3f95-98-51-1-92.ngrok-free.app/ws
{"level":30,"time":1774124694682,"pid":24122,"hostname":"Nathans-MacBook-Pro.local","msg":"Server listening at http://127.0.0.1:8080"}
{"level":30,"time":1774124694684,"pid":24122,"hostname":"Nathans-MacBook-Pro.local","msg":"Server listening at http://[::1]:8080"}
{"level":30,"time":1774124719785,"pid":24122,"hostname":"Nathans-MacBook-Pro.local","reqId":"req-1","req":{"method":"POST","url":"/twiml","host":"3f95-98-51-1-92.ngrok-free.app","remoteAddress":"127.0.0.1","remotePort":63045},"msg":"incoming request"}
{"level":30,"time":1774124719795,"pid":24122,"hostname":"Nathans-MacBook-Pro.local","reqId":"req-1","res":{"statusCode":200},"responseTime":8.668999671936035,"msg":"request completed"}
{"level":30,"time":1774124719985,"pid":24122,"hostname":"Nathans-MacBook-Pro.local","reqId":"req-2","req":{"method":"GET","url":"/ws","host":"3f95-98-51-1-92.ngrok-free.app","remoteAddress":"127.0.0.1","remotePort":63046},"msg":"incoming request"}
Setup for call: CAc4c9a2637f9b5557e273d9a358ee9835
Processing prompt: Today is Saturday, March 21.
Sent response: Thank you for letting me know! Today is Saturday, March twenty first. It is a great day to be out and about if the weather is nice where you are. How can I help you today?
Processing prompt: Please give me an update of local news in San Francisco.
Sent response: I appreciate you asking, but I have to be upfront with you. I don't have access to real-time or current news updates. My knowledge has a cutoff date, and I cannot browse the internet or access live news feeds. So I am not able to give you an accurate local news update for San Francisco today, Saturday, March twenty first.

For the latest local news in San Francisco, I would recommend checking sources like the San Francisco Chronicle, KTVU, NBC Bay Area, or KQED. You can visit their websites or tune in to their broadcasts for up to date local coverage.

Is there anything else I can help you with?
Processing prompt: No. Goodbye.
Sent response: Goodbye! Have a wonderful Saturday, March twenty first. Take care!
WebSocket connection closed
```
