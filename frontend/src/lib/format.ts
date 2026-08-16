/**
 * Locale-aware formatting utilities.
 * All formatters resolve locale from navigator.languages on the client.
 * On the server, a fallback locale is used.
 * Use these instead of hardcoded `.toFixed()` or locale strings.
 */

const SSR_LOCALE = "en-US";

function getLocale(): string {
  if (typeof navigator !== "undefined") {
    return navigator.languages?.[0] ?? SSR_LOCALE;
  }
  return SSR_LOCALE;
}

export function formatTime(ts: number): string {
  return new Intl.DateTimeFormat(getLocale(), {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).format(new Date(ts));
}

export function formatDate(ts: number | string): string {
  return new Intl.DateTimeFormat(getLocale(), {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(new Date(ts));
}

export function formatPercent(value: number | string, decimals = 1): string {
  const num = Number(value);
  if (!Number.isFinite(num)) return "—";
  return new Intl.NumberFormat(getLocale(), {
    style: "percent",
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(num);
}

export function formatNumber(value: number, decimals = 0): string {
  return new Intl.NumberFormat(getLocale(), {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

export function formatRelativeTime(ts: number): string {
  const diff = Date.now() - ts;
  const seconds = Math.floor(diff / 1000);
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return formatDate(ts);
}
