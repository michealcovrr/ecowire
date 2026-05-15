import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatNaira(kobo: number): string {
  const naira = kobo / 100;
  return new Intl.NumberFormat("en-NG", {
    style: "currency",
    currency: "NGN",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(naira);
}

export function formatPhone(phone: string): string {
  const p = phone.replace(/\D/g, "");
  if (p.startsWith("234") && p.length === 13) {
    return `+234 ${p.slice(3, 6)} ${p.slice(6, 9)} ${p.slice(9)}`;
  }
  return `+${p}`;
}

export function normalisePhone(phone: string): string {
  let p = phone.trim().replace(/\s|-/g, "");
  if (p.startsWith("+")) p = p.slice(1);
  if (p.startsWith("0") && p.length === 11) p = "234" + p.slice(1);
  return p;
}
