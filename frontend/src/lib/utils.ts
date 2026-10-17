import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

// Persian (Jalali, Persian digits) while the page is RTL, English once it is switched to LTR.
// Components re-render on a direction change (they call useT), so reading the direction at call time is enough.
const locale = () => (typeof document !== "undefined" && document.documentElement.dir === "ltr" ? "en-US" : "fa-IR");

const cache = new Map<string, Intl.DateTimeFormat | Intl.NumberFormat>();
function fmt<T extends Intl.DateTimeFormat | Intl.NumberFormat>(kind: string, make: (l: string) => T): T {
  const l = locale();
  const key = `${kind}:${l}`;
  let f = cache.get(key);
  if (!f) cache.set(key, (f = make(l)));
  return f as T;
}

export const formatDateTime = (iso: string | null | undefined): string =>
  iso ? fmt("dt", (l) => new Intl.DateTimeFormat(l, { dateStyle: "medium", timeStyle: "short" })).format(new Date(iso)) : "—";
export const formatDate = (iso: string | null | undefined): string =>
  iso ? fmt("d", (l) => new Intl.DateTimeFormat(l, { dateStyle: "medium" })).format(new Date(iso)) : "—";
export const formatNumber = (n: number): string => fmt("n", (l) => new Intl.NumberFormat(l)).format(n);
export const formatPercent = (ratio: number): string => `${formatNumber(Math.round(ratio * 1000) / 10)}${locale() === "en-US" ? "%" : "٪"}`;
