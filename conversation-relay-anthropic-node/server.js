import Fastify from "fastify";
import fastifyWs from "@fastify/websocket";
import fastifyFormBody from '@fastify/formbody';
import Anthropic from "@anthropic-ai/sdk";

const fastify = Fastify({ logger: true });
import dotenv from "dotenv";
dotenv.config();
const PORT = process.env.PORT || 8080;
const DOMAIN = process.env.NGROK_URL;
const WS_URL = `wss://${DOMAIN}/ws`;
const WELCOME_GREETING = "Hi! I am an A I voice assistant powered by Twilio and Anthropic. Ask me anything!";
const SYSTEM_PROMPT = "You are a helpful assistant. This conversation is being translated to voice, so answer carefully. When you respond, please spell out all numbers, for example twenty not 20. Do not include emojis in your responses. Do not include bullet points, asterisks, or special symbols.";
const sessions = new Map();

const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });
const TOOLS = [
  { type: "web_search_20260209", name: "web_search" },
  { type: "web_fetch_20260209", name: "web_fetch" },
];

async function aiResponse(messages) {
  let apiMessages = [...messages];
  let response = await anthropic.messages.create({
    model: "claude-sonnet-4-6",
    max_tokens: 2048,
    messages: apiMessages,
    system: SYSTEM_PROMPT,
    tools: TOOLS,
  });

  // Server-side tool loop can pause when it hits its iteration limit; resume by re-sending
  while (response.stop_reason === "pause_turn") {
    apiMessages = [...apiMessages, { role: "assistant", content: response.content }];
    response = await anthropic.messages.create({
      model: "claude-sonnet-4-6",
      max_tokens: 2048,
      messages: apiMessages,
      system: SYSTEM_PROMPT,
      tools: TOOLS,
    });
  }

  const textBlock = response.content.find(b => b.type === "text");
  return textBlock?.text ?? "";
}

fastify.register(fastifyFormBody);
fastify.register(fastifyWs);
fastify.all("/twiml", async (_, reply) => {
  reply.type("text/xml").send(`<?xml version="1.0" encoding="UTF-8"?><Response><Connect><ConversationRelay url="${WS_URL}" welcomeGreeting="${WELCOME_GREETING}" /></Connect></Response>`);
});
fastify.register(async function (fastify) {
  fastify.get("/ws", { websocket: true }, (ws, _) => {
    ws.on("message", async (data) => {
      const message = JSON.parse(data);
      switch (message.type) {
        case "setup":
          const callSid = message.callSid;
          console.log("Setup for call:", callSid);
          ws.callSid = callSid;
          sessions.set(callSid, []);
          break;
        case "prompt":
          console.log("Processing prompt:", message.voicePrompt);
          try {
            const conversation = sessions.get(ws.callSid);
            conversation.push({ role: "user", content: message.voicePrompt });
            const responseText = await aiResponse(conversation);
            conversation.push({ role: "assistant", content: responseText });
            ws.send(JSON.stringify({ type: "text", token: responseText, last: true }));
            console.log("Sent response:", responseText);
          } catch (err) {
            console.error("Error generating AI response:", err);
            ws.send(JSON.stringify({ type: "text", token: "Sorry, I encountered an error. Please try again.", last: true }));
          }
          break;
        case "interrupt":
          console.log("Handling interruption.");
          break;
        default:
          console.warn("Unknown message type received:", message.type);
          break;
      }
    });
    ws.on("close", () => {
      console.log("WebSocket connection closed");
      sessions.delete(ws.callSid);
    });
  });
});
try {
  fastify.listen({ port: PORT });
  console.log(`Server running at http://localhost:${PORT} and wss://${DOMAIN}/ws`);
} catch (err) {
  fastify.log.error(err);
  process.exit(1);
}
