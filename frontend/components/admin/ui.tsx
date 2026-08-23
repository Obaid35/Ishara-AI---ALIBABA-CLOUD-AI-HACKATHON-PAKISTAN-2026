"use client";

import { useEffect, useState } from "react";

export function PageHeader({
  title,
  description,
  actions,
}: {
  title: string;
  description?: string;
  actions?: React.ReactNode;
}) {
  return (
    <div className="h-16 border-b border-line bg-surface px-6 flex items-center justify-between gap-4 sticky top-0 z-10">
      <div className="min-w-0">
        <h1 className="text-[17px] font-semibold tracking-tight truncate">{title}</h1>
        {description && <p className="text-[12px] text-muted truncate">{description}</p>}
      </div>
      {actions && <div className="flex items-center gap-2 shrink-0">{actions}</div>}
    </div>
  );
}

export function Card({
  title,
  right,
  children,
  className = "",
}: {
  title?: string;
  right?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section className={`card overflow-hidden ${className}`}>
      {title && (
        <div className="px-4 py-3 border-b border-line flex items-center justify-between gap-3">
          <h2 className="text-sm font-semibold">{title}</h2>
          {right}
        </div>
      )}
      {children}
    </section>
  );
}

export function Stat({
  label,
  value,
  hint,
  tone = "default",
}: {
  label: string;
  value: React.ReactNode;
  hint?: string;
  tone?: "default" | "ok" | "warn" | "danger";
}) {
  const tones = {
    default: "text-ink",
    ok: "text-brand",
    warn: "text-amber-600",
    danger: "text-danger",
  };
  return (
    <div className="card px-4 py-3.5">
      <div className="text-[11px] uppercase tracking-wider text-muted font-medium">{label}</div>
      <div className={`text-2xl font-semibold mt-1 tabular-nums ${tones[tone]}`}>{value}</div>
      {hint && <div className="text-[11px] text-muted mt-0.5">{hint}</div>}
    </div>
  );
}

const STATUS_TONE: Record<string, string> = {
  reliable: "pill-ok",
  psl_verified: "pill-ok",
  granted: "pill-ok",
  own_recording: "pill-ok",
  enabled: "pill-ok",
  testing: "pill-info",
  experimenting: "pill-info",
  requested: "pill-info",
  draft: "pill-neutral",
  candidate: "pill-neutral",
  unknown: "pill-neutral",
  weak: "pill-warn",
  stale: "pill-warn",
  dropped: "pill-danger",
  rejected: "pill-danger",
  denied: "pill-danger",
};

export function StatusPill({ value }: { value: string | null | undefined }) {
  if (!value) return <span className="pill-neutral">—</span>;
  const cls = STATUS_TONE[value] ?? "pill-neutral";
  return <span className={cls}>{value.replace(/_/g, " ")}</span>;
}

export function Toast({
  message,
  tone = "ok",
  onDone,
}: {
  message: string | null;
  tone?: "ok" | "warn" | "danger";
  onDone: () => void;
}) {
  useEffect(() => {
    if (!message) return;
    const timer = window.setTimeout(onDone, tone === "ok" ? 3200 : 7000);
    return () => window.clearTimeout(timer);
  }, [message, tone, onDone]);

  if (!message) return null;

  const tones = {
    ok: "bg-brand text-white",
    warn: "bg-amber-500 text-white",
    danger: "bg-danger text-white",
  };

  return (
    <div
      role="status"
      className={`fixed bottom-5 right-5 z-50 max-w-md rounded-xl px-4 py-3 text-sm shadow-lift animate-fade-up ${tones[tone]}`}
    >
      {message}
    </div>
  );
}

/** Inline confirm that shows the consequences before the action is taken. */
export function ConfirmPanel({
  title,
  body,
  confirmLabel,
  onConfirm,
  onCancel,
  busy,
}: {
  title: string;
  body: React.ReactNode;
  confirmLabel: string;
  onConfirm: () => void;
  onCancel: () => void;
  busy?: boolean;
}) {
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-ink/40 p-4">
      <div className="card w-full max-w-lg p-5">
        <h3 className="font-semibold">{title}</h3>
        <div className="text-sm text-muted mt-2 space-y-2">{body}</div>
        <div className="flex justify-end gap-2 mt-5">
          <button onClick={onCancel} className="btn-sm h-10 px-4">
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={busy}
            className="btn h-10 px-4 bg-brand text-white hover:bg-brand-hover text-sm"
          >
            {busy ? "Working…" : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

export function useToast() {
  const [toast, setToast] = useState<{ message: string; tone: "ok" | "warn" | "danger" } | null>(
    null,
  );
  return {
    toast,
    clear: () => setToast(null),
    ok: (message: string) => setToast({ message, tone: "ok" }),
    warn: (message: string) => setToast({ message, tone: "warn" }),
    fail: (message: string) => setToast({ message, tone: "danger" }),
  };
}

export function Empty({ children }: { children: React.ReactNode }) {
  return <div className="px-4 py-10 text-center text-sm text-muted">{children}</div>;
}
