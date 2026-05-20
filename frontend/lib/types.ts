export type AgentId =
  | "triage"
  | "appointment"
  | "insurance"
  | "knowledge"
  | "out_of_scope";

export interface ChatRequest {
  message: string;
  session_key: string;
}

export interface ChatResponse {
  reply: string;
  agent_used: AgentId;
  session_key: string;
}

export type MessageRole = "user" | "assistant" | "system";

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  agent_used?: AgentId;
  createdAt: number;
}
