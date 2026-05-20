import { NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const UPSTREAM_TIMEOUT_MS = 30_000;
const MIN_MESSAGE_LEN = 1;
const MAX_MESSAGE_LEN = 2000;
// Loose UUID-ish check — covers crypto.randomUUID() output but stays permissive
// so the upstream service stays the source of truth on session_key shape.
const SESSION_KEY_RE = /^[A-Za-z0-9_-]{8,128}$/;

interface ChatBody {
  message: string;
  session_key: string;
}

function parseBody(v: unknown): ChatBody | null {
  if (typeof v !== "object" || v === null) return null;
  const o = v as Record<string, unknown>;
  if (typeof o.message !== "string") return null;
  if (typeof o.session_key !== "string") return null;
  const message = o.message.trim();
  if (message.length < MIN_MESSAGE_LEN || message.length > MAX_MESSAGE_LEN) return null;
  if (!SESSION_KEY_RE.test(o.session_key)) return null;
  return { message, session_key: o.session_key };
}

export async function POST(req: Request) {
  const aiServiceUrl = process.env.AI_SERVICE_URL;
  if (!aiServiceUrl) {
    return NextResponse.json({ error: "ai_service_unavailable" }, { status: 502 });
  }

  let raw: unknown;
  try {
    raw = await req.json();
  } catch {
    return NextResponse.json({ error: "invalid_body" }, { status: 400 });
  }

  const body = parseBody(raw);
  if (!body) {
    return NextResponse.json({ error: "invalid_body" }, { status: 400 });
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), UPSTREAM_TIMEOUT_MS);

  try {
    const upstream = await fetch(`${aiServiceUrl.replace(/\/+$/, "")}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: controller.signal,
      cache: "no-store",
    });

    if (!upstream.ok) {
      return NextResponse.json({ error: "ai_service_unavailable" }, { status: 502 });
    }

    const data = (await upstream.json()) as unknown;
    return NextResponse.json(data, { status: 200 });
  } catch {
    return NextResponse.json({ error: "ai_service_unavailable" }, { status: 502 });
  } finally {
    clearTimeout(timer);
  }
}
