"use client";

import { ArrowLeftRight, Moon, Sun } from "lucide-react";
import { useEffect, useState, type MouseEvent } from "react";

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
  const set = () => {
    document.documentElement.dir = dir;
  };
  if (!reducedMotion() && typeof document.startViewTransition === "function") document.startViewTransition(set);
  else set();
}

const btn =
  "relative inline-flex h-9 items-center justify-center gap-1.5 overflow-hidden rounded-md border border-border bg-card px-2.5 text-xs font-medium transition-colors hover:bg-muted";

export function ThemeToggle({ className }: { className?: string }) {
  const [dark, setDark] = useState(false);
  useEffect(() => setDark(document.documentElement.classList.contains("dark")), []);

  function toggle(e: MouseEvent<HTMLButtonElement>) {
    const next = !dark;
    const r = e.currentTarget.getBoundingClientRect();
    setDark(next);
    store("theme", next ? "dark" : "light");
    applyTheme(next, { x: r.left + r.width / 2, y: r.top + r.height / 2 });
  }

  return (
    <button type="button" onClick={toggle} className={cn(btn, "w-9 px-0", className)} aria-label={dark ? "حالت روشن" : "حالت تاریک"} title={dark ? "حالت روشن" : "حالت تاریک"}>
      <Sun className={cn("absolute h-4 w-4 transition-all duration-500", dark ? "rotate-90 scale-0 opacity-0" : "rotate-0 scale-100 opacity-100")} />
      <Moon className={cn("absolute h-4 w-4 transition-all duration-500", dark ? "rotate-0 scale-100 opacity-100" : "-rotate-90 scale-0 opacity-0")} />
    </button>
  );
}

export function DirToggle({ className }: { className?: string }) {
  const [dir, setDir] = useState<"rtl" | "ltr">("rtl");
  const [turns, setTurns] = useState(0);
  useEffect(() => setDir(document.documentElement.dir === "ltr" ? "ltr" : "rtl"), []);

  function toggle() {
    const next = dir === "rtl" ? "ltr" : "rtl";
    setDir(next);
    setTurns((t) => t + 1);
    store("dir", next);
    applyDir(next);
  }

  return (
    <button type="button" onClick={toggle} className={cn(btn, className)} aria-label="تغییر جهت صفحه (راست‌چین / چپ‌چین)" title="تغییر جهت صفحه">
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
