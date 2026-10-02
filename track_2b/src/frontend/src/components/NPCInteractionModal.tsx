"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { io, type Socket } from "socket.io-client";
import type { BackendNPC } from "@/types/backend";

interface ChatMessage {
  role: "user" | "npc";
  content: string;
}

interface NPCInteractionModalProps {
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

const INCOME_LABEL: Record<string, { text: string; color: string }> = {
  low: { text: "LOW", color: "#B83A52" },
  medium: { text: "MED", color: "#C97D1A" },
  high: { text: "HIGH", color: "#3E7C34" },
};

const API_BASE = "http://localhost:8000";

function politicalLabel(v: number): string {
  if (v <= -0.6) return "strongly progressive";
  if (v <= -0.2) return "leaning progressive";
  if (v <= 0.2) return "moderate";
  if (v <= 0.6) return "leaning conservative";
  return "strongly conservative";
}

function politicalColor(v: number): string {
  if (v <= -0.4) return "#5A8DB8";
  if (v <= 0.4) return "#7B68EE";
  return "#B83A52";
}

function StatRow({
  label,
  value,
  valueColor,
}: {
  label: string;
  value: string;
  valueColor?: string;
}) {
  return (
    <div className="flex items-center justify-between py-[3px]">
      <span
        className="text-[9px] font-mono uppercase tracking-widest"
        style={{ color: "#A0824A" }}
      >
        {label}
      </span>
      <span
        className="text-[10px] font-mono font-bold"
        style={{ color: valueColor ?? "#3D2510" }}
      >
        {value}
      </span>
    </div>
  );
}

function SectionBlock({
  label,
  symbol,
  content,
  fallback,
}: {
  label: string;
  symbol: string;
  content?: string;
  fallback: string;
}) {
  const hasContent = content && content.trim().length > 0;
  return (
    <div className="px-3 py-2" style={{ borderTop: "1px solid #E8D5A3" }}>
      <div className="flex items-center gap-1.5 mb-1">
        <span className="text-[10px] font-mono" style={{ color: "#C4A46C" }}>
          {symbol}
        </span>
        <span
          className="text-[8px] font-pixel uppercase"
          style={{ color: "#A0824A" }}
        >
          {label}
        </span>
      </div>
      <p
        className={`text-[10px] font-mono leading-relaxed ${hasContent ? "italic" : ""}`}
        style={{ color: hasContent ? "#6B4C2A" : "#C4A46C" }}
      >
        {hasContent ? `"${content}"` : fallback}
      </p>
    </div>
  );
}

export function NPCInteractionModal({
  npc,
  simulationId,
  onClose,
}: NPCInteractionModalProps) {
  // Chat state
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const socketRef = useRef<Socket | null>(null);

  // Computed values for profile
  const moodColor = MOOD_COLOR[npc.mood] ?? "#8B7355";
  const income = INCOME_LABEL[npc.income_level] ?? INCOME_LABEL.medium;
  const polLabel = politicalLabel(npc.political_leaning);
  const polColor = politicalColor(npc.political_leaning);

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

    socket.on(
      "npc_chat_response",
      (data: { npc_id: string; response: string }) => {
        if (data.npc_id === npc.id) {
          setMessages((prev) => [...prev, { role: "npc", content: data.response }]);
          setIsLoading(false);
        }
      },
    );

    socket.on(
      "npc_chat_error",
      (data: { npc_id: string; message: string }) => {
        if (data.npc_id === npc.id) {
          setError(data.message);
          setIsLoading(false);
        }
      },
    );

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

    const newUserMessage: ChatMessage = { role: "user", content: trimmed };
    setMessages((prev) => [...prev, newUserMessage]);
    setInput("");
    setIsLoading(true);
    setError(null);

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

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center"
      onClick={onClose}
      onKeyDown={(e) => {
        if (e.key === "Escape") onClose();
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="interaction-title"
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" />

      {/* Combined Panel */}
      <article
        className="relative z-10 flex w-[720px] h-[520px] max-h-[85vh] animate-[modalIn_150ms_ease-out]"
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
        {/* Left Panel - Profile */}
        <div
          className="flex flex-col w-[320px] shrink-0 overflow-hidden"
          style={{ borderRight: "3px solid #C4A46C" }}
        >
          {/* Profile Header */}
          <div
            className="flex items-start justify-between px-3 py-3 shrink-0"
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
                  id="interaction-title"
                  className="text-[9px] font-pixel uppercase tracking-wide truncate"
                  style={{ color: "#5B3A1E" }}
                >
                  {npc.name}
                </h2>
              </div>
              <div
                className="mt-1 ml-5 text-[9px] font-mono uppercase tracking-widest"
                style={{ color: "#8B7355" }}
              >
                {npc.profession || npc.role?.replace(/_/g, " ") || "Resident"} ·{" "}
                {npc.mbti} · {npc.industry || npc.lang || "resident"}
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

          {/* Profile Content - Scrollable */}
          <div className="flex-1 overflow-y-auto scrollbar-thin">
            {/* Stats */}
            <div
              className="px-3 py-2"
              style={{
                background: "#EDE4D3",
                borderBottom: "1px solid #E8D5A3",
              }}
            >
              <div className="flex items-center gap-1.5 mb-1">
                <span
                  className="text-[10px] font-mono"
                  style={{ color: "#D4A520" }}
                >
                  {"\u2605"}
                </span>
                <span
                  className="text-[8px] font-pixel uppercase"
                  style={{ color: "#A0824A" }}
                >
                  Status
                </span>
              </div>
              <div className="ml-3">
                <StatRow
                  label="Mood"
                  value={npc.mood.toUpperCase()}
                  valueColor={moodColor}
                />
                <StatRow
                  label="Reputation"
                  value={`${(npc.reputation * 100).toFixed(0)}%`}
                  valueColor="#2dd4bf"
                />
                <StatRow
                  label="Income"
                  value={income.text}
                  valueColor={income.color}
                />
                <StatRow
                  label="Political"
                  value={`${npc.political_leaning > 0 ? "+" : ""}${npc.political_leaning.toFixed(1)} ${polLabel}`}
                  valueColor={polColor}
                />
                <StatRow label="Position" value={`(${npc.x}, ${npc.y})`} />
              </div>
            </div>

            {/* Internal state sections */}
            <SectionBlock
              label="Thinking"
              symbol="?"
              content={npc.perception}
              fallback="No thoughts yet..."
            />
            <SectionBlock
              label="Strategy"
              symbol="#"
              content={npc.current_plan}
              fallback="No strategy formed yet..."
            />
            <SectionBlock
              label="Beliefs"
              symbol="!"
              content={npc.beliefs?.join(" · ")}
              fallback="No defined beliefs..."
            />
            <SectionBlock
              label="Controversial Ideas"
              symbol="*"
              content={npc.controversial_ideas?.join(" · ")}
              fallback="No controversial ideas..."
            />
            <SectionBlock
              label="Feeling"
              symbol="~"
              content={npc.mood}
              fallback="No feelings recorded yet..."
            />
            <SectionBlock
              label="Plan"
              symbol=">"
              content={npc.current_plan}
              fallback="No plan formed yet..."
            />
          </div>

          {/* Profile Footer */}
          <div
            className="px-3 py-2 shrink-0"
            style={{ background: "#E8D5A3", borderTop: "2px solid #C4A46C" }}
          >
            <span
              className="text-[9px] font-mono uppercase tracking-tight"
              style={{ color: "#A0824A" }}
            >
              {npc.id}
            </span>
          </div>
        </div>

        {/* Right Panel - Chat */}
        <div className="flex flex-col flex-1 overflow-hidden">
          {/* Chat Header */}
          <div
            className="flex items-center justify-between px-3 py-3 shrink-0"
            style={{ background: "#E8D5A3", borderBottom: "2px solid #C4A46C" }}
          >
            <div className="flex items-center gap-2">
              <span
                className="text-[10px] font-mono"
                style={{ color: "#A0824A" }}
              >
                {">>"}
              </span>
              <span
                className="text-[9px] font-pixel uppercase tracking-wide"
                style={{ color: "#5B3A1E" }}
              >
                Chat
              </span>
              <span
                className="text-[9px] font-mono uppercase"
                style={{ color: moodColor }}
              >
                [{npc.mood}]
              </span>
            </div>
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
                  className="max-w-[85%] px-3 py-2 rounded"
                  style={{
                    background: msg.role === "user" ? "#E8D5A3" : "#D4E8D4",
                    border: `2px solid ${msg.role === "user" ? "#C4A46C" : "#8BC48B"}`,
                  }}
                >
                  <div
                    className="text-[8px] font-mono uppercase tracking-widest mb-1"
                    style={{
                      color: msg.role === "user" ? "#A0824A" : "#5A8B5A",
                    }}
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
        </div>
      </article>
    </div>
  );
}
