import type { ChatResponse } from "./types";

export class ChatClientError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ChatClientError";
  }
}

export async function sendMessage(
  message: string,
  sessionKey: string,
): Promise<ChatResponse> {
  let res: Response;
  try {
    res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, session_key: sessionKey }),
    });
  } catch {
    throw new ChatClientError("network");
  }

  if (!res.ok) {
    throw new ChatClientError(`http_${res.status}`);
  }

  let data: unknown;
  try {
    data = await res.json();
  } catch {
    throw new ChatClientError("invalid_response");
  }

  if (!isChatResponse(data)) {
    throw new ChatClientError("invalid_response");
  }
  return data;
}

function isChatResponse(v: unknown): v is ChatResponse {
  if (typeof v !== "object" || v === null) return false;
  const o = v as Record<string, unknown>;
  return (
    typeof o.reply === "string" &&
    typeof o.session_key === "string" &&
    typeof o.agent_used === "string"
  );
}
