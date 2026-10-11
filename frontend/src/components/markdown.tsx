"use client";

import "highlight.js/styles/github-dark.css";

import { Check, Copy } from "lucide-react";
import { useRef, useState, type ComponentPropsWithoutRef } from "react";
import ReactMarkdown from "react-markdown";
import rehypeHighlight from "rehype-highlight";
import remarkGfm from "remark-gfm";

function CodeBlock(props: ComponentPropsWithoutRef<"pre">) {
  const ref = useRef<HTMLPreElement>(null);
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(ref.current?.innerText ?? "");
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard unavailable (insecure context) */
    }
  };
  return (
    <div className="group relative" dir="ltr">
      <pre ref={ref} {...props} />
      <button
        type="button"
        onClick={copy}
        aria-label="کپی کد"
        className="absolute right-2 top-2 rounded bg-white/10 p-1.5 text-white opacity-0 transition-opacity hover:bg-white/20 focus-visible:opacity-100 group-hover:opacity-100"
      >
        {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
      </button>
    </div>
  );
}

/**
 * Safe Markdown rendering: raw HTML in the source is never interpreted (no rehype-raw), dangerous URL schemes are
 * dropped by react-markdown's default urlTransform, and links open in a new tab without referrer.
 */
export function Markdown({ content }: { content: string }) {
  return (
    <div className="md" dir="auto">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[[rehypeHighlight, { detect: true, ignoreMissing: true }]]}
        components={{
          pre: CodeBlock,
          a: ({ href, children }) => (
            <a href={href} target="_blank" rel="noopener noreferrer nofollow">
              {children}
            </a>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
