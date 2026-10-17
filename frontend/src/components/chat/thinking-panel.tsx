"use client";

import { Brain } from "lucide-react";
import { useEffect, useRef } from "react";

import { Spinner } from "@/components/ui/misc";
import { useT } from "@/lib/i18n";

/** Collapsible view of the model's reasoning. Open and auto-scrolling while the model is still thinking. */
export function ThinkingPanel({ text, streaming = false }: { text: string; streaming?: boolean }) {
  const t = useT();
  const box = useRef<HTMLPreElement>(null);
  useEffect(() => {
    if (streaming && box.current) box.current.scrollTop = box.current.scrollHeight;
  }, [text, streaming]);

  return (
    <details open={streaming || undefined} className="mb-2 rounded-md border border-border bg-muted/50 text-sm">
      <summary className="flex cursor-pointer select-none items-center gap-2 px-3 py-1.5 text-muted-foreground">
        <Brain className="h-4 w-4" />
        {t(streaming ? "در حال فکر کردن…" : "فرایند تفکر مدل")}
        {streaming ? <Spinner className="h-3 w-3" /> : null}
      </summary>
      <pre
        ref={box}
        dir="auto"
        className="max-h-64 overflow-auto whitespace-pre-wrap break-words border-t border-border px-3 py-2 font-sans text-xs leading-6 text-muted-foreground"
      >
        {text}
      </pre>
    </details>
  );
}
