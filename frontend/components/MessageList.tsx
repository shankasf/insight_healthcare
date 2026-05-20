"use client";

import { useEffect, useRef } from "react";
import type { Message } from "@/lib/types";
import MessageBubble from "./MessageBubble";

interface MessageListProps {
  messages: Message[];
  loading: boolean;
  onSuggestion: (text: string) => void;
}

const SUGGESTIONS = [
  "Book an appointment with Dr. Chen",
  "Do you accept Blue Cross PPO?",
  "What are your hours?",
];

function TypingIndicator() {
  return (
    <div className="flex justify-start" aria-live="polite" aria-label="Assistant is typing">
      <div className="flex items-center gap-1 rounded-2xl rounded-bl-sm bg-gray-100 px-4 py-3 ring-1 ring-inset ring-gray-200">
        <span
          className="h-1.5 w-1.5 animate-dot-bounce rounded-full bg-gray-500"
          style={{ animationDelay: "0ms" }}
        />
        <span
          className="h-1.5 w-1.5 animate-dot-bounce rounded-full bg-gray-500"
          style={{ animationDelay: "150ms" }}
        />
        <span
          className="h-1.5 w-1.5 animate-dot-bounce rounded-full bg-gray-500"
          style={{ animationDelay: "300ms" }}
        />
      </div>
    </div>
  );
}

function EmptyState({ onSuggestion }: { onSuggestion: (text: string) => void }) {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-6 px-4 py-10 text-center">
      <div className="max-w-sm space-y-2">
        <h2 className="text-xl font-semibold text-gray-900 sm:text-2xl">
          Hi — how can I help today?
        </h2>
        <p className="text-sm text-gray-500">
          Ask about appointments, insurance coverage, or anything about our clinic.
        </p>
      </div>
      <ul className="flex flex-wrap justify-center gap-2" aria-label="Suggested questions">
        {SUGGESTIONS.map((text) => (
          <li key={text}>
            <button
              type="button"
              onClick={() => onSuggestion(text)}
              className="rounded-full border border-gray-200 bg-white px-3.5 py-1.5 text-sm text-gray-700 shadow-sm transition hover:border-blue-300 hover:bg-blue-50 hover:text-blue-700 active:scale-[0.98]"
              aria-label={`Use suggestion: ${text}`}
            >
              {text}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function MessageList({ messages, loading, onSuggestion }: MessageListProps) {
  const endRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages.length, loading]);

  const isEmpty = messages.length === 0 && !loading;

  return (
    <div
      className="flex-1 overflow-y-auto"
      role="log"
      aria-live="polite"
      aria-relevant="additions"
    >
      {isEmpty ? (
        <EmptyState onSuggestion={onSuggestion} />
      ) : (
        <div className="mx-auto flex w-full max-w-[720px] flex-col gap-3 px-4 py-6 sm:px-6">
          {messages.map((m) => (
            <MessageBubble key={m.id} message={m} />
          ))}
          {loading ? <TypingIndicator /> : null}
          <div ref={endRef} aria-hidden="true" />
        </div>
      )}
    </div>
  );
}
