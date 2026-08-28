import { useState, useRef, useEffect } from "react";
import MessageBubble from "./MessageBubble";
import ModelBadge from "./ModelBadge";
import { sendMessage } from "../api/client";

const MODES = [
  { id: "chat", label: "💬 Chat" },
  { id: "essay", label: "✍️ Essay" },
  { id: "artifact", label: "📄 Artifact" },
];

function Dot({ ok }) {
  return (
    <span className={`inline-block w-2 h-2 rounded-full ${ok ? "bg-green-400" : "bg-red-400"}`} />
  );
}

export default function ChatPane({ sessionId, setSessionId, setArtifact, health }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [mode, setMode] = useState("chat");
  const [loading, setLoading] = useState(false);
  const [provider, setProvider] = useState("");
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async () => {
    if (!input.trim() || loading) return;
    const text = input;
    setMessages((p) => [...p, { role: "user", content: text }]);
    setInput("");
    setLoading(true);
    try {
      const res = await sendMessage({ message: text, session_id: sessionId, mode });
      if (!sessionId) setSessionId(res.session_id);
      setProvider(res.provider);
      setMessages((p) => [...p, { role: "assistant", content: res.message, sources: res.sources }]);
      if (res.artifact) setArtifact(res.artifact);
    } catch (e) {
      const msg = e?.message === "Failed to fetch" ? "Backend unreachable" : e.message;
      setMessages((p) => [...p, { role: "assistant", content: msg, sources: [] }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800">
        <div>
          <h1 className="font-semibold text-sm">🎙️ Lenny Growth Assistant</h1>
          <div className="flex items-center gap-3 mt-1 text-[11px] text-gray-400">
            <span className="inline-flex items-center gap-1">
              <Dot ok={Boolean(health?.llm_connected)} /> LLM
            </span>
            <span className="inline-flex items-center gap-1">
              <Dot ok={Boolean(health?.chroma_docs > 0)} /> Chroma
            </span>
            <span className="inline-flex items-center gap-1">
              <Dot ok={Boolean(health?.db_connected)} /> DB
            </span>
          </div>
        </div>
        <ModelBadge provider={provider || health?.provider} />
      </div>
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-20 text-sm">
            Ask anything about product growth, retention, or GTM — grounded in Lenny's Podcast.
          </div>
        )}
        {messages.map((m, i) => (
          <MessageBubble key={i} message={m} />
        ))}
        {loading && (
          <div className="flex items-center gap-2 text-gray-400 text-sm">
            <div className="animate-spin w-3 h-3 border border-gray-400 border-t-transparent rounded-full" />
            Thinking...
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <div className="px-4 py-3 border-t border-gray-800 space-y-2">
        <div className="flex gap-2">
          {MODES.map((m) => (
            <button
              key={m.id}
              onClick={() => setMode(m.id)}
              className={`text-xs px-3 py-1 rounded-full ${mode === m.id ? "bg-blue-600 text-white" : "bg-gray-800 text-gray-400 hover:bg-gray-700"}`}
            >
              {m.label}
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
            placeholder={
              mode === "essay"
                ? "Ask a question — get a Ship 30 essay..."
                : "Ask about product growth, retention, GTM..."
            }
            className="flex-1 bg-gray-800 text-gray-100 text-sm rounded-lg px-4 py-2 outline-none focus:ring-1 focus:ring-blue-500 placeholder-gray-500"
          />
          <button
            onClick={send}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-sm px-4 py-2 rounded-lg"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
