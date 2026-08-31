"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import CameraPanel from "@/components/CameraPanel";
import DoctorMode from "@/components/DoctorMode";
import GuidancePanel from "@/components/GuidancePanel";
import Header, { type Mode } from "@/components/Header";
import MessageCard from "@/components/MessageCard";
import SessionHistory from "@/components/SessionHistory";
import StatusBar from "@/components/StatusBar";
import { get, post } from "@/lib/api";
import { useRecognition } from "@/lib/useRecognition";
import type {
  DoctorPhrase,
  Health,
  HistoryTurn,
  Message,
  RecognitionEvent,
  Sign,
} from "@/lib/types";

interface ResolveResponse {
  matched: "exact" | "base" | "none";
  message: Message | null;
  note?: string;
}

export default function CommunicationScreen() {
  const [mode, setMode] = useState<Mode>("patient");
  const [health, setHealth] = useState<Health | null>(null);
  const [signs, setSigns] = useState<Record<string, Sign>>({});

  const [concepts, setConcepts] = useState<string[]>([]);
  const [message, setMessage] = useState<Message | null>(null);
  const [matched, setMatched] = useState<"exact" | "base" | "none" | null>(null);
  const [note, setNote] = useState<string | null>(null);

  const [speaking, setSpeaking] = useState(false);
  const [speechError, setSpeechError] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryTurn[]>([]);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const turnId = useRef(0);

  // ----------------------------------------------------------- bootstrap

  useEffect(() => {
    get<Health>("/api/health", false).then(setHealth).catch(() => setHealth(null));
    get<{ signs: Sign[] }>("/api/signs", false)
      .then((data) =>
        setSigns(Object.fromEntries(data.signs.map((sign) => [sign.code, sign]))),
      )
      .catch(() => setSigns({}));
  }, []);

  // ----------------------------------------------------------- recognition

  const handleResult = useCallback((event: RecognitionEvent) => {
    // Only a recognized sign adds a concept. Unknown and aborted add nothing —
    // that is the whole point of the gate.
    if (event.type === "recognized" && event.sign_code) {
      setConcepts((current) => [...current, event.sign_code!]);
    }
  }, []);

  const recognition = useRecognition(handleResult, mode === "patient");

  // Resolve the concept sequence into a controlled Urdu message.
  useEffect(() => {
    if (concepts.length === 0) {
      setMessage(null);
      setMatched(null);
      setNote(null);
      return;
    }
    let cancelled = false;
    post<ResolveResponse>("/api/messages/resolve", { concepts }, false)
      .then((data) => {
        if (cancelled) return;
        setMessage(data.message);
        setMatched(data.matched);
        setNote(data.note ?? null);
      })
      .catch(() => {
        if (cancelled) return;
        setMessage(null);
        setMatched("none");
        setNote("Could not reach the message service.");
      });
    return () => {
      cancelled = true;
    };
  }, [concepts]);

  // ----------------------------------------------------------- actions

  const speak = useCallback(async () => {
    if (!message) return;
    setSpeechError(null);
    setSpeaking(true);
    try {
      const resolved = await get<{ ok: boolean; url: string | null; reason: string | null }>(
        `/api/speech/resolve/${message.code}`,
        false,
      );
      if (!resolved.ok || !resolved.url) {
        setSpeechError(resolved.reason ?? "Audio is not available for this message.");
        setSpeaking(false);
        return;
      }

      audioRef.current?.pause();
      const audio = new Audio(resolved.url);
      audioRef.current = audio;
      audio.onended = () => setSpeaking(false);
      audio.onerror = () => {
        setSpeechError("The audio file could not be played.");
        setSpeaking(false);
      };
      await audio.play();

      turnId.current += 1;
      setHistory((current) => [
        ...current,
        {
          id: turnId.current,
          speaker: "patient",
          urdu: message.urdu_text,
          english: message.english_text,
          at: Date.now(),
        },
      ]);
    } catch {
      setSpeechError("Could not reach the speech service.");
      setSpeaking(false);
    }
  }, [message]);

  const undo = useCallback(() => {
    setConcepts((current) => current.slice(0, -1));
    setSpeechError(null);
  }, []);

  const clear = useCallback(() => {
    setConcepts([]);
    setSpeechError(null);
    recognition.reset();
  }, [recognition]);

  const newConversation = useCallback(() => {
    setConcepts([]);
    setMessage(null);
    setMatched(null);
    setNote(null);
    setHistory([]);
    setSpeechError(null);
    audioRef.current?.pause();
    setSpeaking(false);
    recognition.reset();
  }, [recognition]);

  const sendPhrase = useCallback((phrase: DoctorPhrase) => {
    turnId.current += 1;
    setHistory((current) => [
      ...current,
      {
        id: turnId.current,
        speaker: "doctor",
        urdu: phrase.urdu_text,
        english: phrase.english_text,
        at: Date.now(),
      },
    ]);
  }, []);

  const conceptUrdu =
    recognition.lastEvent?.sign_code && signs[recognition.lastEvent.sign_code]
      ? signs[recognition.lastEvent.sign_code].urdu_meaning
      : null;

  return (
    <div className="screen-fixed flex flex-col">
      <Header
        mode={mode}
        onModeChange={setMode}
        onNewConversation={newConversation}
        health={health}
      />

      {mode === "patient" ? (
        <main className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-[minmax(0,1.4fr)_minmax(400px,1fr)] gap-4 p-4">
          {/* ------------------------------------------------ camera */}
          <div className="flex flex-col min-h-0">
            <CameraPanel
              videoRef={recognition.videoRef}
              cameraState={recognition.cameraState}
              cameraError={recognition.cameraError}
              status={recognition.status}
              motion={recognition.motion}
              connected={recognition.connected}
              isStub={recognition.isStub}
              onStart={() => void recognition.startCamera()}
            />
          </div>

          {/* ------------------------------------------------ right column */}
          <div className="flex flex-col gap-3 min-h-0">
            <StatusBar
              status={recognition.status}
              event={recognition.lastEvent}
              conceptUrdu={conceptUrdu}
            />

            <MessageCard
              concepts={concepts}
              message={message}
              matched={matched}
              note={note}
              speaking={speaking}
              speechError={speechError}
              onSpeak={() => void speak()}
              onUndo={undo}
              onClear={clear}
            />

            <div className="h-[30%] min-h-[140px] flex flex-col">
              <SessionHistory turns={history} />
            </div>
          </div>
        </main>
      ) : (
        <DoctorMode onSend={sendPhrase} />
      )}

      <footer className="h-9 shrink-0 border-t border-line bg-surface px-5 flex items-center justify-between">
        <p className="text-[11px] text-muted">
          Communication assistance prototype — not diagnostic. Does not provide medical advice.
        </p>
        <p className="text-[11px] text-muted hidden md:block">
          {recognition.vocabularySize > 0 && `${recognition.vocabularySize} verified signs · `}
          No internet required
        </p>
      </footer>

      {/* Renders nothing unless an admin has enabled it. */}
      <GuidancePanel />
    </div>
  );
}
