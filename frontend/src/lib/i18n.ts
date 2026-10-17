"use client";

import { useSyncExternalStore } from "react";

import { EN } from "@/lib/en";

/** Page direction decides the language: RTL = Persian (the source strings), LTR = English. */
export type Dir = "rtl" | "ltr";

const listeners = new Set<() => void>();

function subscribe(cb: () => void) {
  listeners.add(cb);
  return () => void listeners.delete(cb);
}

const snapshot = (): Dir => (document.documentElement.dir === "ltr" ? "ltr" : "rtl");

export function useDir(): Dir {
  return useSyncExternalStore(subscribe, snapshot, () => "rtl");
}

export function setDir(dir: Dir) {
  const root = document.documentElement;
  root.dir = dir;
  root.lang = dir === "ltr" ? "en" : "fa";
  document.title = translate(dir, "دستیار هوشمند DevOps");
  listeners.forEach((l) => l());
}

/** `t("متن فارسی")` returns the English text when the page is LTR; unknown strings stay as written. */
export function translate(dir: Dir, fa: string): string {
  return dir === "ltr" ? (EN[fa] ?? fa) : fa;
}

/** For helpers outside React components: reads the current direction at call time. */
export const tNow = (fa: string): string => translate(typeof document !== "undefined" && document.documentElement.dir === "ltr" ? "ltr" : "rtl", fa);

export function useT() {
  const dir = useDir();
  return (fa: string) => translate(dir, fa);
}
