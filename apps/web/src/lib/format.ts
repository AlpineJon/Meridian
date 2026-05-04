export const fmtUsd = (n: number, opts?: { compact?: boolean }) => {
  if (opts?.compact) {
    if (Math.abs(n) >= 1_000_000) return `$${(n / 1_000_000).toFixed(2)}M`;
    if (Math.abs(n) >= 1_000) return `$${(n / 1_000).toFixed(0)}K`;
  }
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(n);
};

export const fmtUsdSqft = (n: number) => `$${n.toFixed(0)}/sf`;

export const fmtPct = (n: number, decimals = 1) =>
  `${(n * 100).toFixed(decimals)}%`;

export const fmtPctDelta = (n: number, decimals = 1) => {
  const v = (n * 100).toFixed(decimals);
  if (n > 0) return `+${v}%`;
  return `${v}%`;
};

export const fmtNum = (n: number, opts?: { compact?: boolean; decimals?: number }) => {
  if (opts?.compact) {
    if (Math.abs(n) >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
    if (Math.abs(n) >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  }
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: opts?.decimals ?? 0,
  }).format(n);
};

export const fmtDays = (n: number) => `${n}d`;
export const fmtMonths = (n: number) => `${n.toFixed(1)} mo`;

/** ISO month "2026-04" -> "Apr '26" */
export const fmtMonthShort = (iso: string) => {
  const [y, m] = iso.split("-").map(Number);
  const d = new Date(Date.UTC(y, m - 1, 1));
  return `${d.toLocaleString("en-US", { month: "short", timeZone: "UTC" })} '${String(y).slice(-2)}`;
};

export const fmtRelativeDate = (iso: string) => {
  const d = new Date(iso);
  const today = new Date();
  const diffDays = Math.floor((today.getTime() - d.getTime()) / 86_400_000);
  if (diffDays === 0) return "today";
  if (diffDays === 1) return "1 day ago";
  if (diffDays < 30) return `${diffDays} days ago`;
  if (diffDays < 60) return "1 month ago";
  return `${Math.floor(diffDays / 30)} months ago`;
};
