"use client";

import type { RecognitionEvent, RecognitionEventType } from "@/lib/types";

/**
 * Status is never conveyed by colour alone — every state carries an icon and
 * text. The two unknown states are deliberately distinct: amber means the
 * system nearly had it, red means it did not.
 */

const ICONS: Record<string, React.ReactNode> = {
  check: (
    <path d="M20 6 9 17l-5-5" />
  ),
  dots: (
    <>
      <circle cx="5" cy="12" r="1.6" />
      <circle cx="12" cy="12" r="1.6" />
      <circle cx="19" cy="12" r="1.6" />
    </>
  ),
  repeat: (
    <>
      <path d="M17 2.1 21 6l-4 3.9" />
      <path d="M3 11V9a4 4 0 0 1 4-4h14M7 21.9 3 18l4-3.9" />
      <path d="M21 13v2a4 4 0 0 1-4 4H3" />
    </>
  ),
  cross: <path d="M18 6 6 18M6 6l12 12" />,
  wave: (
    <>
      <path d="M2 12h3l3-8 4 16 3-8h7" />
    </>
  ),
};

interface StatusStyle {
  label: string;
  urdu: string;
  detail?: string;
  className: string;
  icon: keyof typeof ICONS;
}

function styleFor(status: RecognitionEventType, event: RecognitionEvent | null): StatusStyle {
  switch (status) {
    case "capturing":
      return {
        label: "Reading sign…",
        urdu: "اشارہ سمجھا جا رہا ہے…",
        className: "bg-blue-50 text-info border-info/25",
        icon: "wave",
      };
    case "analyzing":
      return {
        label: "Analyzing",
        urdu: "تجزیہ ہو رہا ہے…",
        className: "bg-blue-50 text-info border-info/25",
        icon: "dots",
      };
    case "recognized":
      return {
        label: "Recognized",
        urdu: "اشارہ سمجھ لیا گیا",
        className: "bg-brand-soft text-brand border-brand/25",
        icon: "check",
      };
    case "unknown_ambiguous":
      return {
        label: "Please repeat the sign",
        urdu: "براہِ کرم اشارہ دوبارہ کریں",
        detail: "Two signs looked too similar. Nothing was added.",
        className: "bg-amber-50 text-amber-700 border-warn/30",
        icon: "repeat",
      };
    case "unknown_no_match":
      return {
        label: "Sign not recognized",
        urdu: "اشارہ سمجھ نہیں آیا",
        detail: "Nothing was added to the message.",
        className: "bg-red-50 text-danger border-danger/25",
        icon: "cross",
      };
    case "aborted":
      return {
        label: "Please sign again",
        urdu: "براہِ کرم دوبارہ اشارہ کریں",
        detail: event?.reason ?? undefined,
        className: "bg-amber-50 text-amber-700 border-warn/30",
        icon: "repeat",
      };
    default:
      return {
        label: "Ready to sign",
        urdu: "اشارہ کرنے کے لیے تیار",
        className: "bg-slate-50 text-muted border-line",
        icon: "wave",
      };
  }
}

export default function StatusBar({
  status,
  event,
  conceptUrdu,
}: {
  status: RecognitionEventType;
  event: RecognitionEvent | null;
  conceptUrdu?: string | null;
}) {
  const style = styleFor(status, event);
  const recognized = status === "recognized" && event?.sign_code;

  return (
    <div className={`rounded-card border px-4 py-3 transition-colors ${style.className}`}>
      <div className="flex items-start gap-3">
        <svg viewBox="0 0 24 24" className="w-5 h-5 mt-0.5 shrink-0" fill="none"
             stroke="currentColor" strokeWidth="2.1" strokeLinecap="round" strokeLinejoin="round"
             aria-hidden="true">
          {ICONS[style.icon]}
        </svg>

        <div className="min-w-0 flex-1">
          <div className="flex items-baseline justify-between gap-3">
            <span className="font-semibold text-[15px]">{style.label}</span>
            <span className="urdu text-sm opacity-80 shrink-0">{style.urdu}</span>
          </div>

          {recognized && (
            <div className="mt-2 flex items-center justify-between gap-3 animate-fade-up">
              <span className="font-mono text-xs px-2 py-1 rounded-md bg-white/70 border border-current/15">
                {event!.sign_code}
              </span>
              {conceptUrdu && <span className="urdu text-concept font-semibold">{conceptUrdu}</span>}
            </div>
          )}

          {style.detail && !recognized && (
            <p className="text-[13px] mt-1 opacity-80">{style.detail}</p>
          )}
        </div>
      </div>
    </div>
  );
}
