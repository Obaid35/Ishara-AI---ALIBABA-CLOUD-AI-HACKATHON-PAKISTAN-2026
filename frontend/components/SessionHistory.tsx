"use client";

import type { HistoryTurn } from "@/lib/types";

/**
 * Shown during a consultation so both sides can see what has been said.
 *
 * Temporary by design — this lives in memory only and is cleared when the
 * session ends. There is no transcript table and nothing reaches the database.
 */
export default function SessionHistory({ turns }: { turns: HistoryTurn[] }) {
  return (
    <section className="card flex flex-col min-h-0">
      <div className="flex items-center justify-between px-4 py-3 border-b border-line shrink-0">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-muted">
          This conversation
        </h2>
        <span className="pill-neutral" title="History is kept in memory only and cleared when the session ends. Nothing is stored.">
          <svg viewBox="0 0 24 24" className="w-3 h-3" fill="none" stroke="currentColor"
               strokeWidth="2.2" strokeLinecap="round" aria-hidden="true">
            <rect x="3" y="11" width="18" height="10" rx="2" />
            <path d="M7 11V7a5 5 0 0 1 10 0v4" />
          </svg>
          Not stored
        </span>
      </div>

      <div className="scroll-area flex-1 min-h-0 p-3 space-y-2">
        {turns.length === 0 ? (
          <p className="text-[13px] text-muted text-center py-6 px-4">
            Messages spoken to the doctor and questions sent to the patient appear here.
          </p>
        ) : (
          turns.map((turn) => {
            const patient = turn.speaker === "patient";
            return (
              <div
                key={turn.id}
                className={`rounded-xl px-3.5 py-2.5 border animate-fade-up ${
                  patient
                    ? "bg-brand-soft border-brand/20"
                    : "bg-blue-50/60 border-info/20"
                }`}
              >
                <div className="flex items-center gap-1.5 mb-1">
                  <span
                    className={`text-[10px] font-semibold uppercase tracking-wider ${
                      patient ? "text-brand" : "text-info"
                    }`}
                  >
                    {patient ? "Patient" : "Doctor"}
                  </span>
                </div>
                <p className="urdu text-[17px] leading-relaxed text-ink">{turn.urdu}</p>
                {turn.english && (
                  <p className="text-[12px] text-muted mt-0.5">{turn.english}</p>
                )}
              </div>
            );
          })
        )}
      </div>
    </section>
  );
}
