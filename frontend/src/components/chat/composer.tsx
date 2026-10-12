"use client";

import { ArrowUp } from "lucide-react";
import { useEffect, useLayoutEffect, useRef, type KeyboardEvent, type ReactNode } from "react";

import { Spinner } from "@/components/ui/misc";
import { cn } from "@/lib/utils";

const MAX_HEIGHT = 240; // px, then the textarea scrolls

interface Props {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  busy: boolean;
  placeholder: string;
  /** when set the box is locked (e.g. documents are still being indexed) and this text is shown instead of the placeholder */
  lockedReason?: string;
  /** extra control rendered just before the send button (token usage) */
  trailing?: ReactNode;
}

/** Auto-growing message box. Enter sends, Shift+Enter inserts a new line; pasted logs keep their line breaks. */
export function Composer({ value, onChange, onSubmit, busy, placeholder, lockedReason, trailing }: Props) {
  const locked = !!lockedReason;
  const ref = useRef<HTMLTextAreaElement>(null);

  // grow with the content (also shrinks again after sending / clearing)
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, MAX_HEIGHT)}px`;
    el.style.overflowY = el.scrollHeight > MAX_HEIGHT ? "auto" : "hidden";
  }, [value]);

  // give focus back when an answer finished
  useEffect(() => {
    if (!busy) ref.current?.focus();
  }, [busy]);

  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      if (!busy && !locked && value.trim()) onSubmit();
    }
  }

  const canSend = !busy && !locked && value.trim().length > 0;
  return (
    <div
      className={cn(
        "flex items-end gap-2 rounded-2xl border border-border bg-background px-3 py-2 shadow-sm transition-shadow",
        "focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/30",
        (busy || locked) && "opacity-70",
      )}
    >
      <textarea
        ref={ref}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={onKeyDown}
        dir="auto"
        data-bare
        rows={1}
        readOnly={busy || locked}
        spellCheck={false}
        aria-label="پیام"
        placeholder={lockedReason ?? placeholder}
        className="max-h-60 min-h-[2.5rem] flex-1 resize-none bg-transparent py-2 text-[0.95rem] leading-6 placeholder:text-muted-foreground focus:outline-none focus-visible:ring-0 focus-visible:ring-offset-0"
      />
      {trailing}
      <button
        type="button"
        onClick={onSubmit}
        disabled={!canSend}
        aria-label="ارسال پیام"
        title="ارسال (Enter)"
        className="mb-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground transition-all hover:bg-primary/90 disabled:cursor-not-allowed disabled:bg-muted disabled:text-muted-foreground"
      >
        {busy ? <Spinner /> : <ArrowUp className="h-4 w-4" />}
      </button>
    </div>
  );
}
