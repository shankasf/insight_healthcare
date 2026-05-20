"use client";

import type { AgentId, Message } from "@/lib/types";

interface AgentBadgeMeta {
  label: string;
  className: string;
}

const AGENT_BADGES: Record<AgentId, AgentBadgeMeta> = {
  triage: {
    label: "Triage",
    className: "bg-slate-100 text-slate-700 ring-slate-200",
  },
  appointment: {
    label: "Appointment agent",
    className: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  },
  insurance: {
    label: "Insurance agent",
    className: "bg-violet-50 text-violet-700 ring-violet-200",
  },
  knowledge: {
    label: "Knowledge agent",
    className: "bg-sky-50 text-sky-700 ring-sky-200",
  },
  out_of_scope: {
    label: "Out of scope",
    className: "bg-amber-50 text-amber-700 ring-amber-200",
  },
};

function AgentPill({ agent }: { agent: AgentId }) {
  const meta = AGENT_BADGES[agent];
  return (
    <span
      className={`mt-1.5 inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium ring-1 ring-inset ${meta.className}`}
    >
      <span
        aria-hidden="true"
        className="h-1.5 w-1.5 rounded-full bg-current opacity-70"
      />
      {meta.label}
    </span>
  );
}

export default function MessageBubble({ message }: { message: Message }) {
  if (message.role === "system") {
    return (
      <div className="flex justify-center">
        <p
          role="status"
          className="rounded-full bg-red-50 px-3 py-1 text-xs font-medium text-red-700 ring-1 ring-inset ring-red-200"
        >
          {message.content}
        </p>
      </div>
    );
  }

  const isUser = message.role === "user";

  return (
    <div
      className={`flex animate-bubble-in ${isUser ? "justify-end" : "justify-start"}`}
    >
      <div className={`flex max-w-[85%] flex-col ${isUser ? "items-end" : "items-start"}`}>
        <div
          className={[
            "whitespace-pre-wrap break-words rounded-2xl px-4 py-2.5 text-sm leading-relaxed shadow-sm",
            isUser
              ? "rounded-br-sm bg-blue-600 text-white"
              : "rounded-bl-sm bg-gray-100 text-gray-900 ring-1 ring-inset ring-gray-200",
          ].join(" ")}
        >
          {message.content}
        </div>
        {!isUser && message.agent_used ? (
          <AgentPill agent={message.agent_used} />
        ) : null}
      </div>
    </div>
  );
}
