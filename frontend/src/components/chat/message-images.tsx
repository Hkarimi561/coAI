"use client";

import { X } from "lucide-react";
import { useEffect, useState } from "react";

import { useT } from "@/lib/i18n";

/** Thumbnails of the screenshots attached to a message; click one to view it full size. */
export function MessageImages({ urls }: { urls: string[] }) {
  const t = useT();
  const [open, setOpen] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(null);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  if (!urls.length) return null;
  return (
    <>
      <div className="mb-2 flex flex-wrap gap-2">
        {urls.map((u) => (
          <button key={u} type="button" onClick={() => setOpen(u)} className="overflow-hidden rounded-md border border-border bg-muted" title={t("نمایش تصویر")}>
            {/* eslint-disable-next-line @next/next/no-img-element -- authenticated API image / local blob URL, not optimizable by next/image */}
            <img src={u} alt={t("تصویر پیوست")} loading="lazy" className="max-h-48 max-w-full object-contain" />
          </button>
        ))}
      </div>
      {open ? (
        <div role="dialog" aria-modal="true" aria-label={t("تصویر پیوست")} className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4" onClick={() => setOpen(null)}>
          <button type="button" aria-label={t("بستن")} className="absolute end-4 top-4 rounded-full bg-black/60 p-2 text-white hover:bg-black/80" onClick={() => setOpen(null)}>
            <X className="h-5 w-5" />
          </button>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={open} alt={t("تصویر پیوست")} className="max-h-full max-w-full rounded-md object-contain" onClick={(e) => e.stopPropagation()} />
        </div>
      ) : null}
    </>
  );
}
