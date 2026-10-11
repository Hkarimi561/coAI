import { ApiError } from "@/lib/api";
import type { Message } from "@/lib/types";

export interface StreamHandlers {
  onUserMessage?: (m: Message) => void;
  onStatus?: (step: string) => void;
  onToken?: (text: string) => void;
  onThinking?: (text: string) => void;
  onDone?: (m: Message) => void;
}

/** POSTs a chat message and consumes the Server-Sent Events response. Rejects on transport or server `error` events. */
export async function streamMessage(conversationId: string, content: string, h: StreamHandlers): Promise<void> {
  const res = await fetch(`/api/chat/conversations/${conversationId}/messages`, {
    method: "POST",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify({ content }),
  });
  if (!res.ok || !res.body) {
    let detail = res.statusText;
    try {
      const body = (await res.json()) as { detail?: string };
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, detail || `HTTP ${res.status}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let finished = false;

  const dispatch = (raw: string) => {
    let event = "message";
    const data: string[] = [];
    for (const line of raw.split("\n")) {
      if (line.startsWith("event:")) event = line.slice(6).trim();
      else if (line.startsWith("data:")) data.push(line.slice(5).trimStart());
    }
    if (!data.length) return; // comment / keep-alive
    const payload = JSON.parse(data.join("\n")) as Record<string, unknown>;
    switch (event) {
      case "user_message":
        h.onUserMessage?.(payload as unknown as Message);
        break;
      case "status":
        h.onStatus?.(String(payload.step ?? ""));
        break;
      case "thinking":
        h.onThinking?.(String(payload.text ?? ""));
        break;
      case "token":
        h.onToken?.(String(payload.text ?? ""));
        break;
      case "done":
        finished = true;
        h.onDone?.(payload as unknown as Message);
        break;
      case "error":
        throw new Error(String(payload.message ?? "خطای ناشناخته"));
    }
  };

  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let idx: number;
    while ((idx = buffer.indexOf("\n\n")) !== -1) {
      const raw = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      dispatch(raw);
    }
  }
  if (!finished) throw new Error("ارتباط با سرور قطع شد؛ صفحه را تازه‌سازی کنید (پاسخ در صورت تکمیل ذخیره می‌شود).");
}
