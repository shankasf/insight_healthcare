"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Stethoscope } from "lucide-react";
import { sendMessage } from "@/lib/chatClient";
import { getOrCreateSessionKey } from "@/lib/sessionKey";
import type { Message } from "@/lib/types";
import MessageList from "./MessageList";
import MessageInput, { type MessageInputHandle } from "./MessageInput";

function newId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

export default function ChatWindow() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionKey, setSessionKey] = useState<string>("");

  const inputRef = useRef<MessageInputHandle | null>(null);

  useEffect(() => {
    setSessionKey(getOrCreateSessionKey());
  }, []);

  const handleSubmit = useCallback(
    async (text: string) => {
      if (!sessionKey || loading) return;

      const userMessage: Message = {
        id: newId(),
        role: "user",
        content: text,
        createdAt: Date.now(),
      };
      setMessages((prev) => [...prev, userMessage]);
      setDraft("");
      setLoading(true);

      try {
        const res = await sendMessage(text, sessionKey);
        setMessages((prev) => [
          ...prev,
          {
            id: newId(),
            role: "assistant",
            content: res.reply,
            agent_used: res.agent_used,
            createdAt: Date.now(),
          },
        ]);
      } catch {
        setMessages((prev) => [
          ...prev,
          {
            id: newId(),
            role: "system",
            content: "Something went wrong — please try again.",
            createdAt: Date.now(),
          },
        ]);
      } finally {
        setLoading(false);
      }
    },
    [sessionKey, loading],
  );

  const handleSuggestion = useCallback((text: string) => {
    setDraft(text);
    inputRef.current?.focus();
  }, []);

  return (
    <main className="flex h-[100dvh] w-full justify-center bg-gray-50 sm:p-4">
      <section
        className="flex h-full w-full max-w-[760px] flex-col overflow-hidden bg-white sm:rounded-2xl sm:border sm:border-gray-200 sm:shadow-sm"
        aria-label="Insight Healthcare Clinic assistant"
      >
        <header className="sticky top-0 z-10 flex items-center gap-3 border-b border-gray-200 bg-white/95 px-4 py-3 backdrop-blur sm:px-6 sm:py-4">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-blue-50 text-blue-600 ring-1 ring-inset ring-blue-100">
            <Stethoscope className="h-5 w-5" aria-hidden="true" />
          </div>
          <div className="min-w-0 flex-1">
            <h1 className="truncate text-sm font-semibold text-gray-900 sm:text-base">
              Insight Healthcare Clinic
            </h1>
            <p className="hidden truncate text-xs text-gray-500 sm:block">
              Ask about appointments, insurance, or our clinic.
            </p>
          </div>
          <div
            className="flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1 text-[11px] font-medium text-emerald-700 ring-1 ring-inset ring-emerald-200"
            aria-label="Assistant is online"
          >
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
            </span>
            online
          </div>
        </header>

        <MessageList
          messages={messages}
          loading={loading}
          onSuggestion={handleSuggestion}
        />

        <MessageInput
          ref={inputRef}
          value={draft}
          onChange={setDraft}
          onSubmit={handleSubmit}
          disabled={loading || !sessionKey}
        />
      </section>
    </main>
  );
}
