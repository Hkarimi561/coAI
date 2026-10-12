"use client";

import { Download, ExternalLink, FileText } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { CITATION_LABEL } from "@/lib/labels";
import type { Citation } from "@/lib/types";

const TONE = { doc: "info", lesson: "success", solution: "success", github: "info", web: "warning", docker: "neutral", ci: "neutral" } as const;

export function CitationList({ citations }: { citations: Citation[] }) {
  if (!citations.length) return null;
  const cited = citations.filter((c) => c.cited);
  const rest = citations.filter((c) => !c.cited);
  return (
    <div className="mt-3 space-y-2 border-t border-border pt-3">
      <h4 className="text-xs font-semibold text-muted-foreground">منابع</h4>
      <ul className="space-y-1.5">{(cited.length ? cited : citations).map((c) => <CitationRow key={c.n} c={c} />)}</ul>
      {cited.length && rest.length ? (
        <details className="text-xs">
          <summary className="cursor-pointer text-muted-foreground">منابع بررسی‌شده‌ی دیگر ({rest.length.toLocaleString("fa-IR")})</summary>
          <ul className="mt-1.5 space-y-1.5">{rest.map((c) => <CitationRow key={c.n} c={c} />)}</ul>
        </details>
      ) : null}
    </div>
  );
}

function downloadUrl(path: string): string {
  return `/api/chat/documents/download?path=${encodeURIComponent(path)}`;
}

function CitationRow({ c }: { c: Citation }) {
  return (
    <li className="text-sm">
      <details className="group rounded-md border border-border bg-muted/40 px-2.5 py-1.5">
        <summary className="flex cursor-pointer list-none flex-wrap items-center gap-2">
          <span className="ltr rounded bg-primary/10 px-1.5 text-xs font-semibold text-primary">[{c.n}]</span>
          <Badge tone={TONE[c.kind]}>
            {CITATION_LABEL[c.kind]}
            {c.kind === "web" && c.origin ? ` · ${c.origin === "cache" ? "کش" : "جدید"}` : ""}
          </Badge>
          <span className="font-medium" dir="auto">
            {c.title}
          </span>
          {c.location ? (
            <span className="text-xs text-muted-foreground" dir="auto">
              {c.location}
            </span>
          ) : null}
          {c.kind === "doc" && c.path ? (
            <a
              href={downloadUrl(c.path)}
              download
              onClick={(e) => e.stopPropagation()}
              className="ms-auto inline-flex items-center gap-1 rounded-md border border-border bg-card px-2 py-0.5 text-xs text-primary hover:bg-muted"
              title="دانلود فایل کامل Markdown"
            >
              <Download className="h-3 w-3" /> دانلود .md
            </a>
          ) : null}
        </summary>
        <div className="mt-2 space-y-1.5">
          {c.url ? (
            <a href={c.url} target="_blank" rel="noopener noreferrer nofollow" className="ltr inline-flex items-center gap-1 text-xs text-primary underline">
              <ExternalLink className="h-3 w-3" /> {c.url}
            </a>
          ) : null}
          {c.path ? (
            <div className="ltr inline-flex items-center gap-1 text-xs text-muted-foreground">
              <FileText className="h-3 w-3" /> {c.path}
            </div>
          ) : null}
          <pre className="max-h-48 overflow-auto whitespace-pre-wrap rounded bg-card p-2 text-xs text-left">{c.snippet}</pre>
        </div>
      </details>
    </li>
  );
}
