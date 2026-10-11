import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

const dateTime = new Intl.DateTimeFormat("fa-IR", { dateStyle: "medium", timeStyle: "short" });
const dateOnly = new Intl.DateTimeFormat("fa-IR", { dateStyle: "medium" });
const number = new Intl.NumberFormat("fa-IR");

export const formatDateTime = (iso: string | null | undefined): string => (iso ? dateTime.format(new Date(iso)) : "—");
export const formatDate = (iso: string | null | undefined): string => (iso ? dateOnly.format(new Date(iso)) : "—");
export const formatNumber = (n: number): string => number.format(n);
export const formatPercent = (ratio: number): string => `${number.format(Math.round(ratio * 1000) / 10)}٪`;
