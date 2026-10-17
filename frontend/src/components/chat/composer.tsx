"use client";

import { ArrowUp, ImagePlus, Plug, Wrench, X } from "lucide-react";
import { useEffect, useLayoutEffect, useMemo, useRef, useState, type KeyboardEvent, type ReactNode } from "react";

import { Spinner } from "@/components/ui/misc";
import type { McpCommand } from "@/lib/types";
import { tNow, useT } from "@/lib/i18n";
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
  /** MCP slash commands for the autocomplete: `/server request` and `/server@tool request` */
  commands?: McpCommand[];
  /** screenshots queued for the next message (local preview URLs); omit `onAddFiles` to hide the attach controls */
  attachments?: { url: string; name: string }[];
  onAddFiles?: (files: File[]) => void;
  onRemoveAttachment?: (index: number) => void;
}

const imagesOf = (files: FileList | File[] | null | undefined): File[] => Array.from(files ?? []).filter((f) => f.type.startsWith("image/"));

interface Suggestion {
  insert: string;
  label: string;
  hint: string;
  kind: "server" | "tool";
}

/** Suggestions for the first word of the message when it starts with "/". */
function suggest(token: string | null, commands: McpCommand[]): Suggestion[] {
  if (token === null || !commands.length) return [];
  const t = token.toLowerCase();
  const out: Suggestion[] = [];
  const toolSug = (c: McpCommand, tool: McpCommand["tools"][number]): Suggestion => ({
    insert: `/${c.server}@${tool.name} `,
    label: `/${c.server}@${tool.name}`,
    hint: tool.destructive ? `⚠ ${tNow("تغییر وضعیت")} — ${tool.description}` : tool.description,
    kind: "tool",
  });
  if (t.includes("@")) {
    const [srv, prefix = ""] = t.split("@");
    const c = commands.find((x) => x.server === srv);
    if (c) out.push(...c.tools.filter((x) => x.name.toLowerCase().startsWith(prefix)).map((x) => toolSug(c, x)));
    return out;
  }
  for (const c of commands.filter((x) => x.server.startsWith(t))) {
    out.push({
      insert: `/${c.server} `,
      label: `/${c.server}`,
      hint: c.hint || `${tNow("ابزارها:")} ${c.tools.map((x) => x.name).join(", ")}`,
      kind: "server",
    });
    if (c.server === t) out.push(...c.tools.map((x) => toolSug(c, x))); // exact server typed: also offer its tools
  }
  return out;
}

/** Auto-growing message box. Enter sends, Shift+Enter inserts a new line; pasted logs keep their line breaks.
 *  Typing "/" opens an autocomplete of MCP servers; "/server@" lists that server's tools. */
export function Composer({ value, onChange, onSubmit, busy, placeholder, lockedReason, trailing, commands = [], attachments = [], onAddFiles, onRemoveAttachment }: Props) {
  const t = useT();
  const locked = !!lockedReason;
  const ref = useRef<HTMLTextAreaElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const canAttach = !!onAddFiles && !busy && !locked;
  const [caret, setCaret] = useState(0);
  const [active, setActive] = useState(0);
  const [dismissed, setDismissed] = useState<string | null>(null);

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

  // the command word: text between the leading "/" and the first whitespace, only while the caret is inside it
  const word = /^\/(\S*)/.exec(value);
  const token = word && caret <= word[0].length ? (word[1] ?? "") : null;
  const suggestions = useMemo(() => suggest(token, commands), [token, commands]);
  const open = !busy && !locked && suggestions.length > 0 && dismissed !== value;
  const signature = suggestions.map((s) => s.label).join("|");
  useEffect(() => setActive(0), [signature]);

  function apply(s: Suggestion) {
    const rest = value.slice(word ? word[0].length : 0).replace(/^\s+/, "");
    const next = s.insert + rest;
    onChange(next);
    setDismissed(null);
    requestAnimationFrame(() => {
      const el = ref.current;
      if (!el) return;
      el.focus();
      el.setSelectionRange(s.insert.length, s.insert.length);
      setCaret(s.insert.length);
    });
  }

  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.nativeEvent.isComposing) return;
    if (open) {
      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        e.preventDefault();
        const n = suggestions.length;
        setActive((i) => (e.key === "ArrowDown" ? (i + 1) % n : (i - 1 + n) % n));
        return;
      }
      if (e.key === "Enter" || e.key === "Tab") {
        e.preventDefault();
        const pick = suggestions[Math.min(active, suggestions.length - 1)];
        if (pick) apply(pick);
        return;
      }
      if (e.key === "Escape") {
        e.preventDefault();
        setDismissed(value);
        return;
      }
    }
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!busy && !locked && (value.trim() || attachments.length)) onSubmit();
    }
  }

  const canSend = !busy && !locked && (value.trim().length > 0 || attachments.length > 0);
  return (
    <div
      className={cn(
        "relative flex flex-col gap-2 rounded-2xl border border-border bg-background px-3 py-2 shadow-sm transition-shadow",
        "focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/30",
        (busy || locked) && "opacity-70",
        dragging && "border-primary ring-2 ring-primary/30",
      )}
      onDragOver={(e) => {
        if (!canAttach || !Array.from(e.dataTransfer.types).includes("Files")) return;
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        setDragging(false);
        const files = imagesOf(e.dataTransfer.files);
        if (!canAttach || !files.length) return;
        e.preventDefault();
        onAddFiles?.(files);
      }}
    >
      {attachments.length ? (
        <ul className="flex flex-wrap gap-2" aria-label={t("تصاویر پیوست")}>
          {attachments.map((a, i) => (
            <li key={a.url} className="group relative">
              {/* eslint-disable-next-line @next/next/no-img-element -- local blob preview */}
              <img src={a.url} alt={a.name} className="h-16 w-16 rounded-md border border-border object-cover" />
              {onRemoveAttachment && !busy ? (
                <button
                  type="button"
                  onClick={() => onRemoveAttachment(i)}
                  aria-label={`${t("حذف")} ${a.name}`}
                  className="absolute -end-1.5 -top-1.5 flex h-5 w-5 items-center justify-center rounded-full bg-foreground text-background shadow hover:bg-danger"
                >
                  <X className="h-3 w-3" />
                </button>
              ) : null}
            </li>
          ))}
        </ul>
      ) : null}
      <div className="flex items-end gap-2">
      {open ? (
        <div role="listbox" aria-label={t("دستورهای MCP")} className="absolute bottom-full start-0 end-0 z-30 mb-2 overflow-hidden rounded-lg border border-border bg-card shadow-lg">
          <div className="max-h-64 overflow-y-auto py-1">
            {suggestions.map((s, i) => (
              <button
                key={s.label}
                type="button"
                role="option"
                aria-selected={i === active}
                onMouseDown={(e) => {
                  e.preventDefault(); // keep focus in the textarea
                  apply(s);
                }}
                onMouseEnter={() => setActive(i)}
                className={cn("flex w-full items-baseline gap-2 px-3 py-1.5 text-start text-sm", i === active ? "bg-primary/10" : "hover:bg-muted", s.kind === "tool" && "ps-7")}
              >
                {s.kind === "server" ? <Plug className="h-3.5 w-3.5 shrink-0 translate-y-0.5 text-primary" /> : <Wrench className="h-3.5 w-3.5 shrink-0 translate-y-0.5 text-muted-foreground" />}
                <code dir="ltr" className="shrink-0 font-semibold">
                  {s.label}
                </code>
                <span className="min-w-0 flex-1 truncate text-xs text-muted-foreground" dir="auto">
                  {s.hint}
                </span>
              </button>
            ))}
          </div>
          <div className="border-t border-border bg-muted/50 px-3 py-1 text-[11px] text-muted-foreground">
            {t("↑↓ انتخاب · Enter / Tab تأیید · Esc بستن · برای انتخاب ابزار بعد از نام سرور @ بزنید")}
          </div>
        </div>
      ) : null}
      {onAddFiles ? (
        <>
          <input
            ref={fileRef}
            type="file"
            accept="image/png,image/jpeg,image/webp,image/gif"
            multiple
            hidden
            onChange={(e) => {
              const files = imagesOf(e.target.files);
              if (files.length) onAddFiles(files);
              e.target.value = ""; // allow picking the same file again
            }}
          />
          <button
            type="button"
            onClick={() => fileRef.current?.click()}
            disabled={!canAttach}
            aria-label={t("پیوست تصویر")}
            title={t("پیوست تصویر (می‌توانید تصویر را اینجا Paste یا Drop هم کنید)")}
            className="mb-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-muted hover:text-foreground disabled:cursor-not-allowed disabled:opacity-50"
          >
            <ImagePlus className="h-5 w-5" />
          </button>
        </>
      ) : null}
      <textarea
        ref={ref}
        value={value}
        onPaste={(e) => {
          const files = imagesOf(e.clipboardData.files);
          if (!canAttach || !files.length) return; // plain text pastes keep their default behaviour
          e.preventDefault();
          onAddFiles?.(files);
        }}
        onChange={(e) => {
          onChange(e.target.value);
          setCaret(e.target.selectionStart);
          setDismissed(null);
        }}
        onSelect={(e) => setCaret(e.currentTarget.selectionStart)}
        onKeyDown={onKeyDown}
        dir="auto"
        data-bare
        rows={1}
        readOnly={busy || locked}
        spellCheck={false}
        aria-label={t("پیام")}
        aria-autocomplete="list"
        placeholder={lockedReason ?? placeholder}
        className="max-h-60 min-h-[2.5rem] flex-1 resize-none bg-transparent py-2 text-[0.95rem] leading-6 placeholder:text-muted-foreground focus:outline-none focus-visible:ring-0 focus-visible:ring-offset-0"
      />
      {trailing}
      <button
        type="button"
        onClick={onSubmit}
        disabled={!canSend}
        aria-label={t("ارسال پیام")}
        title={t("ارسال (Enter)")}
        className="mb-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground transition-all hover:bg-primary/90 disabled:cursor-not-allowed disabled:bg-muted disabled:text-muted-foreground"
      >
        {busy ? <Spinner /> : <ArrowUp className="h-4 w-4" />}
      </button>
      </div>
    </div>
  );
}
