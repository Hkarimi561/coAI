"use client";

import { ArrowLeftRight, Moon, Sun } from "lucide-react";
import { useEffect, useState, type MouseEvent } from "react";

import { setDir, useDir, useT } from "@/lib/i18n";
import { cn } from "@/lib/utils";

const reducedMotion = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;

function store(key: string, value: string) {
  try {
    localStorage.setItem(key, value);
  } catch {
    /* private mode: preference just won't persist */
  }
}

function applyTheme(dark: boolean, origin?: { x: number; y: number }) {
  const root = document.documentElement;
  const set = () => {
    root.classList.toggle("dark", dark);
    root.style.colorScheme = dark ? "dark" : "light";
  };
  if (reducedMotion()) return set();

  if (origin && typeof document.startViewTransition === "function") {
    // circular reveal growing from the clicked button
    const radius = Math.hypot(Math.max(origin.x, innerWidth - origin.x), Math.max(origin.y, innerHeight - origin.y));
    root.classList.add("theme-reveal");
    const transition = document.startViewTransition(set);
    void transition.ready.then(() => {
      root.animate(
        { clipPath: [`circle(0px at ${origin.x}px ${origin.y}px)`, `circle(${radius}px at ${origin.x}px ${origin.y}px)`] },
        { duration: 600, easing: "cubic-bezier(.4,0,.2,1)", pseudoElement: "::view-transition-new(root)" },
      );
    });
    void transition.finished.finally(() => root.classList.remove("theme-reveal"));
    return;
  }
  root.classList.add("theme-anim");
  set();
  setTimeout(() => root.classList.remove("theme-anim"), 450);
}

function applyDir(dir: "rtl" | "ltr") {
  const set = () => setDir(dir);
  if (!reducedMotion() && typeof document.startViewTransition === "function") document.startViewTransition(set);
  else set();
}

const btn =
  "relative inline-flex h-9 items-center justify-center gap-1.5 overflow-hidden rounded-md border border-border bg-card px-2.5 text-xs font-medium transition-colors hover:bg-muted";

export function ThemeToggle({ className }: { className?: string }) {
  const t = useT();
  const [dark, setDark] = useState(false);
  useEffect(() => {
    setDark(document.documentElement.classList.contains("dark"));
    // until the user picks a mode, follow the operating system (also when it changes while the page is open)
    const mq = matchMedia("(prefers-color-scheme: dark)");
    const follow = () => {
      let saved: string | null = null;
      try {
        saved = localStorage.getItem("theme");
      } catch {
        /* ignore */
      }
      if (saved) return;
      setDark(mq.matches);
      applyTheme(mq.matches);
    };
    mq.addEventListener("change", follow);
    return () => mq.removeEventListener("change", follow);
  }, []);

  function toggle(e: MouseEvent<HTMLButtonElement>) {
    const next = !dark;
    const r = e.currentTarget.getBoundingClientRect();
    setDark(next);
    store("theme", next ? "dark" : "light");
    applyTheme(next, { x: r.left + r.width / 2, y: r.top + r.height / 2 });
  }

  return (
    <button type="button" onClick={toggle} className={cn(btn, "w-9 px-0", className)} aria-label={t(dark ? "حالت روشن" : "حالت تاریک")} title={t(dark ? "حالت روشن" : "حالت تاریک")}>
      <Sun className={cn("absolute h-4 w-4 transition-all duration-500", dark ? "rotate-90 scale-0 opacity-0" : "rotate-0 scale-100 opacity-100")} />
      <Moon className={cn("absolute h-4 w-4 transition-all duration-500", dark ? "rotate-0 scale-100 opacity-100" : "-rotate-90 scale-0 opacity-0")} />
    </button>
  );
}

export function DirToggle({ className }: { className?: string }) {
  const t = useT();
  const dir = useDir();
  const [turns, setTurns] = useState(0);

  function toggle() {
    const next = dir === "rtl" ? "ltr" : "rtl";
    setTurns((t) => t + 1);
    store("dir", next);
    applyDir(next);
  }

  return (
    <button type="button" onClick={toggle} className={cn(btn, className)} aria-label={t("تغییر جهت صفحه (راست‌چین / چپ‌چین)")} title={t("تغییر جهت صفحه")}>
      <ArrowLeftRight className="h-4 w-4 transition-transform duration-500" style={{ transform: `rotate(${turns * 180}deg)` }} />
      <span className="ltr font-mono tracking-wide">{dir.toUpperCase()}</span>
    </button>
  );
}

export function Preferences({ className }: { className?: string }) {
  return (
    <div className={cn("flex items-center gap-2", className)}>
      <DirToggle />
      <ThemeToggle />
    </div>
  );
}
