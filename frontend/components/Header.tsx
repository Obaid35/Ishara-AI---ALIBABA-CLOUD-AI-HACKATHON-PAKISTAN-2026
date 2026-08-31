"use client";

import Image from "next/image";
import Link from "next/link";
import { useAuth } from "@/lib/auth";
import type { Health } from "@/lib/types";

export type Mode = "patient" | "doctor";

interface Props {
  mode: Mode;
  onModeChange: (mode: Mode) => void;
  onNewConversation: () => void;
  health: Health | null;
}

function Logo() {
  return (
    <div className="flex items-center gap-2.5">
      {/* The mark alone — the name is set below in the UI face rather than
          baked into the image, so it stays sharp and translatable. */}
      <Image
        src="/ishara-mark-192.png"
        alt=""
        width={192}
        height={192}
        priority
        className="w-9 h-9 shrink-0 object-contain"
      />
      <div className="leading-tight">
        <div className="font-semibold text-[15px] tracking-tight">Ishara AI</div>
        <div className="text-[11px] text-muted -mt-0.5">Healthcare communication</div>
      </div>
    </div>
  );
}

/** Never hidden: the team must know which path is live without guessing. */
function DegradedChip({ health }: { health: Health | null }) {
  if (!health || health.degradations.length === 0) return null;

  const snapshot = health.database.mode === "snapshot";
  const label = snapshot ? "Snapshot mode" : "Limited mode";

  return (
    <div
      className="pill-warn cursor-help"
      title={health.degradations.join("\n")}
      aria-label={`${label}. ${health.degradations.join(". ")}`}
    >
      <svg viewBox="0 0 24 24" className="w-3.5 h-3.5" fill="none" stroke="currentColor"
           strokeWidth="2.2" strokeLinecap="round" aria-hidden="true">
        <path d="M12 9v4M12 17h.01" />
        <path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z" />
      </svg>
      {label}
      <span className="hidden lg:inline font-normal opacity-70">
        · {health.degradations.length}
      </span>
    </div>
  );
}

export default function Header({ mode, onModeChange, onNewConversation, health }: Props) {
  const { user, signOut } = useAuth();

  const tab = (value: Mode, label: string, icon: React.ReactNode) => {
    const active = mode === value;
    return (
      <button
        onClick={() => onModeChange(value)}
        aria-pressed={active}
        className={`flex items-center gap-2 h-10 px-4 rounded-lg text-sm font-medium transition-colors ${
          active
            ? "bg-brand text-white shadow-sm"
            : "text-muted hover:text-ink hover:bg-brand-soft"
        }`}
      >
        {icon}
        <span className="hidden sm:inline">{label}</span>
      </button>
    );
  };

  return (
    <header className="h-16 shrink-0 bg-surface border-b border-line px-4 lg:px-6 flex items-center gap-4">
      <Logo />

      <nav className="flex items-center gap-1 p-1 bg-page rounded-xl border border-line ml-2">
        {tab(
          "patient",
          "Patient → Doctor",
          <svg viewBox="0 0 24 24" className="w-4 h-4" fill="none" stroke="currentColor"
               strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M9 11V6a1.5 1.5 0 0 1 3 0v5M12 10V5.5a1.5 1.5 0 0 1 3 0V11" />
            <path d="M9 11V9a1.5 1.5 0 0 0-3 0v4a8 8 0 0 0 8 8 7 7 0 0 0 7-7v-4a1.5 1.5 0 0 0-3 0" />
          </svg>,
        )}
        {tab(
          "doctor",
          "Doctor → Patient",
          <svg viewBox="0 0 24 24" className="w-4 h-4" fill="none" stroke="currentColor"
               strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M6 3v6a6 6 0 0 0 12 0V3" />
            <path d="M6 3H4M18 3h2M12 15v2a4 4 0 0 0 8 0v-1" />
            <circle cx="20" cy="14" r="2" />
          </svg>,
        )}
      </nav>

      <div className="flex-1" />

      <DegradedChip health={health} />

      <button onClick={onNewConversation} className="btn-sm gap-1.5 h-10 px-3.5">
        <svg viewBox="0 0 24 24" className="w-4 h-4" fill="none" stroke="currentColor"
             strokeWidth="2" strokeLinecap="round" aria-hidden="true">
          <path d="M12 5v14M5 12h14" />
        </svg>
        <span className="hidden md:inline">New Conversation</span>
      </button>

      {user ? (
        <div className="flex items-center gap-2 pl-3 border-l border-line">
          <div className="text-right hidden lg:block leading-tight">
            <div className="text-sm font-medium">{user.full_name || user.email}</div>
            <div className="text-[11px] text-muted capitalize">{user.role}</div>
          </div>
          {user.role === "admin" && (
            <Link href="/admin" className="btn-sm h-10 px-3">
              Admin
            </Link>
          )}
          <button onClick={() => void signOut()} className="btn-sm h-10 px-3 text-muted">
            Sign out
          </button>
        </div>
      ) : (
        // Staff sign-in is offered, never required — the patient must be able
        // to use this screen with no account at all.
        <Link href="/login" className="btn-sm h-10 px-3.5 pl-3 border-line">
          Staff sign in
        </Link>
      )}
    </header>
  );
}
