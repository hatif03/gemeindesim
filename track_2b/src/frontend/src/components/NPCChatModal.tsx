"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { io, type Socket } from "socket.io-client";
import type { BackendNPC } from "@/types/backend";

interface ChatMessage {
  role: "user" | "npc";
  content: string;
}

interface NPCChatModalProps {
  npc: BackendNPC;
  simulationId: string;
  onClose: () => void;
}

const MOOD_COLOR: Record<string, string> = {
  angry: "#B83A52",
  anxious: "#C97D1A",
  worried: "#C97D1A",
  neutral: "#5A8DB8",
  hopeful: "#3E7C34",
  excited: "#7B68EE",
};

const API_BASE = "http://localhost:8000";

export function NPCChatModal({ npc, simulationId, onClose }: NPCChatModalProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const socketRef = useRef<Socket | null>(null);

  // Scroll to bottom when messages change
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  // biome-ignore lint/correctness/useExhaustiveDependencies: scroll on message count change
  useEffect(() => {
    scrollToBottom();
  }, [messages.length, scrollToBottom]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Set up Socket.IO connection for chat
  useEffect(() => {
    const socket = io(API_BASE, {
      transports: ["websocket"],
      reconnection: true,
      reconnectionAttempts: 3,
    });

    socket.on("npc_chat_response", (data: { npc_id: string; response: string }) => {
      if (data.npc_id === npc.id) {
        setMessages(prev => [...prev, { role: "npc", content: data.response }]);
        setIsLoading(false);
      }
    });

    socket.on("npc_chat_error", (data: { npc_id: string; message: string }) => {
      if (data.npc_id === npc.id) {
        setError(data.message);
        setIsLoading(false);
      }
    });

    socketRef.current = socket;

    return () => {
      socket.disconnect();
    };
  }, [npc.id]);

  // Handle ESC key
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  const sendMessage = useCallback(() => {
    const trimmed = input.trim();
    if (!trimmed || isLoading || !socketRef.current) return;

    // Add user message to UI
    const newUserMessage: ChatMessage = { role: "user", content: trimmed };
    setMessages(prev => [...prev, newUserMessage]);
    setInput("");
    setIsLoading(true);
    setError(null);

    // Send to backend
    socketRef.current.emit("chat_with_npc", {
      simulation_id: simulationId,
      npc_id: npc.id,
      message: trimmed,
      history: [...messages, newUserMessage],
    });
  }, [input, isLoading, messages, npc.id, simulationId]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    },
    [sendMessage],
  );

  const moodColor = MOOD_COLOR[npc.mood] ?? "#8B7355";

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center"
      onClick={onClose}
      onKeyDown={(e) => { if (e.key === "Escape") onClose(); }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="chat-title"
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" />

      {/* Panel */}
      <article
        className="relative z-10 flex flex-col w-[400px] h-[500px] max-h-[80vh] animate-[modalIn_150ms_ease-out]"
        style={{
          background: "#F5E6C8",
          border: "4px solid #6B4226",
          borderRadius: "8px",
          boxShadow:
            "inset 2px 2px 0 rgba(196,164,108,.55), inset -2px -2px 0 rgba(61,37,16,.25), 4px 4px 0 rgba(61,37,16,.4)",
        }}
        onClick={(e) => e.stopPropagation()}
        onKeyDown={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          className="flex items-center justify-between px-3 py-3 shrink-0"
          style={{ background: "#E8D5A3", borderBottom: "2px solid #C4A46C" }}
        >
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <span
                className="text-[10px] font-mono"
                style={{ color: "#A0824A" }}
              >
                {">>"}
              </span>
              <h2
                id="chat-title"
                className="text-[9px] font-pixel uppercase tracking-wide truncate"
                style={{ color: "#5B3A1E" }}
              >
                Chat with {npc.name}
              </h2>
            </div>
            <div
              className="mt-1 ml-5 flex items-center gap-2 text-[9px] font-mono uppercase tracking-widest"
              style={{ color: "#8B7355" }}
            >
              <span>{npc.profession}</span>
              <span style={{ color: moodColor }}>[{npc.mood}]</span>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-[10px] font-mono px-1 -mr-1 uppercase transition-opacity hover:opacity-60"
            style={{ color: "#8B7355" }}
          >
            [{"\u00D7"}]
          </button>
        </div>

        {/* Messages */}
        <div
          className="flex-1 overflow-y-auto px-3 py-2 space-y-3"
          style={{ background: "#FDF5E6" }}
        >
          {messages.length === 0 && (
            <div
              className="text-center py-8 text-[9px] font-mono uppercase tracking-widest"
              style={{ color: "#C4A46C" }}
            >
              Start a conversation with {npc.name}...
            </div>
          )}

          {messages.map((msg, idx) => (
            <div
              key={`${msg.role}-${idx}-${msg.content.slice(0, 10)}`}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className="max-w-[80%] px-3 py-2 rounded"
                style={{
                  background: msg.role === "user" ? "#E8D5A3" : "#D4E8D4",
                  border: `2px solid ${msg.role === "user" ? "#C4A46C" : "#8BC48B"}`,
                }}
              >
                <div
                  className="text-[8px] font-mono uppercase tracking-widest mb-1"
                  style={{ color: msg.role === "user" ? "#A0824A" : "#5A8B5A" }}
                >
                  {msg.role === "user" ? "You" : npc.name}
                </div>
                <p
                  className="text-[10px] font-mono leading-relaxed"
                  style={{ color: "#3D2510" }}
                >
                  {msg.content}
                </p>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div
                className="px-3 py-2 rounded"
                style={{
                  background: "#D4E8D4",
                  border: "2px solid #8BC48B",
                }}
              >
                <div
                  className="text-[8px] font-mono uppercase tracking-widest mb-1"
                  style={{ color: "#5A8B5A" }}
                >
                  {npc.name}
                </div>
                <p
                  className="text-[10px] font-mono animate-pulse"
                  style={{ color: "#5A8B5A" }}
                >
                  Thinking...
                </p>
              </div>
            </div>
          )}

          {error && (
            <div
              className="text-center py-2 text-[9px] font-mono"
              style={{ color: "#B83A52" }}
            >
              Error: {error}
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div
          className="px-3 py-2 shrink-0"
          style={{ background: "#E8D5A3", borderTop: "2px solid #C4A46C" }}
        >
          <div className="flex gap-2">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Say something..."
              disabled={isLoading}
              className="flex-1 px-3 py-2 text-[10px] font-mono rounded outline-none disabled:opacity-50"
              style={{
                background: "#FDF5E6",
                border: "2px solid #C4A46C",
                color: "#3D2510",
              }}
            />
            <button
              type="button"
              onClick={sendMessage}
              disabled={isLoading || !input.trim()}
              className="px-4 py-2 text-[9px] font-pixel uppercase tracking-wide transition-opacity hover:opacity-80 disabled:opacity-50"
              style={{
                background: "#3E7C34",
                border: "2px solid #2A5424",
                borderRadius: "4px",
                color: "#FDF5E6",
                boxShadow: "inset 1px 1px 0 #5A9B4A, 2px 2px 0 #1A3414",
              }}
            >
              Send
            </button>
          </div>
          <div
            className="mt-2 text-[8px] font-mono uppercase tracking-widest text-center"
            style={{ color: "#A0824A" }}
          >
            ESC to close | ENTER to send
          </div>
        </div>
      </article>
    </div>
  );
}
