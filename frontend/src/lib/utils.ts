import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(value: number | string | null): string {
  if (value === null || value === undefined) return "—";
  const num = typeof value === "string" ? parseFloat(value) : value;
  if (isNaN(num)) return String(value);
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(num);
}

export function formatValue(value: number | string | null, fieldType: string): string {
  if (value === null || value === undefined) return "—";
  if (fieldType === "currency") return formatCurrency(value);
  if (fieldType === "percentage") return `${value}%`;
  return String(value);
}

export function docTypeLabel(type: string | null): string {
  const labels: Record<string, string> = {
    rent_roll: "Rent Roll",
    operating_statement: "Operating Statement",
    tax_document: "Tax Document",
    unknown: "Unknown",
  };
  return type ? (labels[type] ?? type) : "Unclassified";
}
