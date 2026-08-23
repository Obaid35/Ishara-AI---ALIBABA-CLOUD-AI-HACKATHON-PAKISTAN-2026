"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { get } from "@/lib/api";
import type { DoctorPhrase, PhraseCategory } from "@/lib/types";

interface Props {
  onSend: (phrase: DoctorPhrase) => void;
}

export default function DoctorMode({ onSend }: Props) {
  const [categories, setCategories] = useState<PhraseCategory[]>([]);
  const [selected, setSelected] = useState<DoctorPhrase | null>(null);
  const [query, setQuery] = useState("");
  const [activeCategory, setActiveCategory] = useState<string>("all");
  const [videoMissing, setVideoMissing] = useState(false);
  const [loading, setLoading] = useState(true);
  const videoRef = useRef<HTMLVideoElement | null>(null);

  useEffect(() => {
    get<{ categories: PhraseCategory[] }>("/api/doctor-phrases", false)
      .then((data) => setCategories(data.categories))
      .catch(() => setCategories([]))
      .finally(() => setLoading(false));
  }, []);

  const visible = useMemo(() => {
    const term = query.trim().toLowerCase();
    return categories
      .filter((c) => activeCategory === "all" || c.code === activeCategory)
      .map((c) => ({
        ...c,
        phrases: c.phrases.filter(
          (p) =>
            !term ||
            p.english_text.toLowerCase().includes(term) ||
            p.urdu_text.includes(query.trim()),
        ),
      }))
      .filter((c) => c.phrases.length > 0);
  }, [categories, query, activeCategory]);

  const choose = (phrase: DoctorPhrase) => {
    setSelected(phrase);
    setVideoMissing(false);
    onSend(phrase);
    window.setTimeout(() => videoRef.current?.play().catch(() => undefined), 60);
  };

  const videoSrc = selected?.video_path
    ? `/media/psl-videos/${selected.video_path.split("/").pop()}`
    : null;

  return (
    <div className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-[minmax(0,1.35fr)_minmax(340px,1fr)] gap-4 p-4">
      {/* ---------------------------------------------------- PSL video */}
      <section className="flex flex-col gap-3 min-h-0">
        <div className="relative flex-1 min-h-0 rounded-card overflow-hidden bg-camera border border-line flex items-center justify-center">
          {selected && videoSrc && !videoMissing ? (
            <video
              ref={videoRef}
              key={selected.code}
              src={videoSrc}
              controls
              playsInline
              onError={() => setVideoMissing(true)}
              className="w-full h-full object-contain bg-black"
            />
          ) : (
            <div className="text-center px-8 max-w-md">
              <div className="w-16 h-16 rounded-2xl bg-white/10 flex items-center justify-center mx-auto mb-4">
                <svg viewBox="0 0 24 24" className="w-8 h-8 text-white/70" fill="none"
                     stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"
                     strokeLinejoin="round" aria-hidden="true">
                  <path d="m10 8 6 4-6 4V8z" />
                  <rect x="2" y="3" width="20" height="18" rx="2.5" />
                </svg>
              </div>
              {videoMissing ? (
                <>
                  <p className="text-white/90 font-medium">PSL video is missing</p>
                  <p className="text-white/55 text-sm mt-2">
                    This phrase is enabled but its verified video file is not on disk at{" "}
                    <span className="font-mono text-xs">{selected?.video_path}</span>. Add the
                    verified recording before the demo.
                  </p>
                </>
              ) : (
                <>
                  <p className="text-white/90 font-medium">Choose a question</p>
                  <p className="text-white/55 text-sm mt-2">
                    Select a verified phrase and its PSL video will play here for the patient.
                  </p>
                </>
              )}
            </div>
          )}
        </div>

        {selected && (
          <div className="card px-5 py-4 animate-fade-up">
            <p className="urdu text-concept font-semibold text-ink">{selected.urdu_text}</p>
            <p className="text-sm text-muted mt-1">{selected.english_text}</p>
          </div>
        )}
      </section>

      {/* ---------------------------------------------------- phrase library */}
      <section className="card flex flex-col min-h-0">
        <div className="p-3 border-b border-line space-y-2.5 shrink-0">
          <div className="relative">
            <svg viewBox="0 0 24 24" className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted"
                 fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
              <circle cx="11" cy="11" r="7" />
              <path d="m20 20-3.5-3.5" />
            </svg>
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search questions…"
              className="input pl-9"
              aria-label="Search doctor questions"
            />
          </div>

          <div className="flex gap-1.5 flex-wrap">
            {[{ code: "all", name_en: "All" }, ...categories].map((category) => {
              const active = activeCategory === category.code;
              return (
                <button
                  key={category.code}
                  onClick={() => setActiveCategory(category.code)}
                  className={`px-3 h-8 rounded-lg text-xs font-medium border transition-colors ${
                    active
                      ? "bg-brand text-white border-brand"
                      : "bg-surface text-muted border-line hover:bg-brand-soft hover:text-brand"
                  }`}
                >
                  {category.name_en}
                </button>
              );
            })}
          </div>
        </div>

        <div className="scroll-area flex-1 min-h-0 p-3 space-y-4">
          {loading ? (
            <p className="text-sm text-muted text-center py-8">Loading phrases…</p>
          ) : visible.length === 0 ? (
            <p className="text-sm text-muted text-center py-8 px-4">
              {categories.length === 0
                ? "No verified phrases are enabled yet. Enable them in the admin console."
                : "No phrases match your search."}
            </p>
          ) : (
            visible.map((category) => (
              <div key={category.code}>
                <div className="flex items-baseline justify-between mb-2 px-1">
                  <h3 className="text-[11px] font-semibold uppercase tracking-wider text-muted">
                    {category.name_en}
                  </h3>
                  <span className="urdu text-xs text-muted">{category.name_ur}</span>
                </div>
                <div className="space-y-1.5">
                  {category.phrases.map((phrase) => {
                    const active = selected?.code === phrase.code;
                    return (
                      <button
                        key={phrase.code}
                        onClick={() => choose(phrase)}
                        className={`w-full text-left rounded-xl border px-3.5 py-3 transition-colors ${
                          active
                            ? "border-brand bg-brand-soft"
                            : "border-line bg-surface hover:border-brand/40 hover:bg-brand-soft/50"
                        }`}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <span className="text-sm font-medium text-ink">
                            {phrase.english_text}
                          </span>
                          {active && (
                            <svg viewBox="0 0 24 24" className="w-4 h-4 text-brand shrink-0 mt-0.5"
                                 fill="none" stroke="currentColor" strokeWidth="2.5"
                                 strokeLinecap="round" aria-hidden="true">
                              <path d="M20 6 9 17l-5-5" />
                            </svg>
                          )}
                        </div>
                        <p className="urdu text-[17px] text-ink/85 mt-1">{phrase.urdu_text}</p>
                      </button>
                    );
                  })}
                </div>
              </div>
            ))
          )}
        </div>
      </section>
    </div>
  );
}
