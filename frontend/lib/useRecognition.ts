"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { RecognitionEvent, RecognitionEventType } from "./types";

/**
 * Camera capture + motion reporting + the recognition socket.
 *
 * Motion energy is computed here from a downscaled frame difference. In the
 * finished system the backend derives motion from normalised MediaPipe
 * landmarks instead; the socket protocol does not change when that lands.
 *
 * The segmentation state machine and the unknown gate live on the server —
 * this hook only reports motion and renders what comes back.
 */

const SAMPLE_W = 64;
const SAMPLE_H = 48;
const SEND_HZ = 15;

export type CameraState = "idle" | "starting" | "ready" | "denied" | "unavailable";

export interface UseRecognition {
  videoRef: React.RefObject<HTMLVideoElement | null>;
  cameraState: CameraState;
  cameraError: string | null;
  connected: boolean;
  status: RecognitionEventType;
  lastEvent: RecognitionEvent | null;
  motion: number;
  isStub: boolean;
  vocabularySize: number;
  startCamera: () => Promise<void>;
  stopCamera: () => void;
  reset: () => void;
  arm: (sign: string | null, outcome?: string) => void;
}

export function useRecognition(
  onResult: (event: RecognitionEvent) => void,
  enabled: boolean,
): UseRecognition {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const previousRef = useRef<Uint8ClampedArray | null>(null);
  const timerRef = useRef<number | null>(null);
  const resultRef = useRef(onResult);

  const [cameraState, setCameraState] = useState<CameraState>("idle");
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [connected, setConnected] = useState(false);
  const [status, setStatus] = useState<RecognitionEventType>("ready");
  const [lastEvent, setLastEvent] = useState<RecognitionEvent | null>(null);
  const [motion, setMotion] = useState(0);
  const [isStub, setIsStub] = useState(true);
  const [vocabularySize, setVocabularySize] = useState(0);

  useEffect(() => {
    resultRef.current = onResult;
  }, [onResult]);

  // ------------------------------------------------------------- camera

  const startCamera = useCallback(async () => {
    if (streamRef.current) return;
    setCameraState("starting");
    setCameraError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: "user" },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play().catch(() => undefined);
      }
      setCameraState("ready");
    } catch (error) {
      const name = (error as DOMException)?.name;
      if (name === "NotAllowedError" || name === "SecurityError") {
        setCameraState("denied");
        setCameraError(
          "Camera permission was denied. Allow camera access in the browser, then try again.",
        );
      } else if (name === "NotFoundError" || name === "DevicesNotFoundError") {
        setCameraState("unavailable");
        setCameraError("No camera was found. Connect a camera and try again.");
      } else {
        setCameraState("unavailable");
        setCameraError(`The camera could not be started. ${name ?? ""}`.trim());
      }
    }
  }, []);

  const stopCamera = useCallback(() => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    setCameraState("idle");
  }, []);

  // ------------------------------------------------------------- socket

  useEffect(() => {
    if (!enabled) return;

    const url =
      typeof window !== "undefined"
        ? `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.hostname}:8000/ws/recognize`
        : "";
    if (!url) return;

    let closed = false;
    let socket: WebSocket;
    try {
      socket = new WebSocket(url);
    } catch {
      return;
    }
    socketRef.current = socket;

    socket.onopen = () => !closed && setConnected(true);
    socket.onclose = () => {
      if (!closed) {
        setConnected(false);
        setStatus("ready");
      }
    };
    socket.onerror = () => !closed && setConnected(false);
    socket.onmessage = (raw) => {
      let event: RecognitionEvent;
      try {
        event = JSON.parse(raw.data as string) as RecognitionEvent;
      } catch {
        return;
      }
      setLastEvent(event);
      if (typeof event.is_stub === "boolean") setIsStub(event.is_stub);
      if (typeof event.vocabulary_size === "number") setVocabularySize(event.vocabulary_size);
      setStatus(event.type);
      if (
        event.type === "recognized" ||
        event.type === "unknown_ambiguous" ||
        event.type === "unknown_no_match" ||
        event.type === "aborted"
      ) {
        resultRef.current(event);
      }
    };

    return () => {
      closed = true;
      socket.close();
      socketRef.current = null;
      setConnected(false);
    };
  }, [enabled]);

  // ------------------------------------------------------------- motion loop

  useEffect(() => {
    if (!enabled || cameraState !== "ready") return;

    if (!canvasRef.current) {
      canvasRef.current = document.createElement("canvas");
      canvasRef.current.width = SAMPLE_W;
      canvasRef.current.height = SAMPLE_H;
    }
    const context = canvasRef.current.getContext("2d", { willReadFrequently: true });
    if (!context) return;

    const tick = () => {
      const video = videoRef.current;
      if (!video || video.readyState < 2) return;

      context.drawImage(video, 0, 0, SAMPLE_W, SAMPLE_H);
      const frame = context.getImageData(0, 0, SAMPLE_W, SAMPLE_H).data;

      let energy = 0;
      const previous = previousRef.current;
      if (previous) {
        let total = 0;
        // Luminance-only difference over every 4th pixel — cheap and stable.
        for (let i = 0; i < frame.length; i += 16) {
          const now = frame[i] * 0.299 + frame[i + 1] * 0.587 + frame[i + 2] * 0.114;
          const before = previous[i] * 0.299 + previous[i + 1] * 0.587 + previous[i + 2] * 0.114;
          total += Math.abs(now - before);
        }
        energy = total / (frame.length / 16) / 255;
      }
      previousRef.current = frame;
      setMotion(energy);

      const socket = socketRef.current;
      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: "motion", value: energy }));
      }
    };

    timerRef.current = window.setInterval(tick, 1000 / SEND_HZ);
    return () => {
      if (timerRef.current) window.clearInterval(timerRef.current);
      timerRef.current = null;
      previousRef.current = null;
    };
  }, [enabled, cameraState]);

  useEffect(() => () => stopCamera(), [stopCamera]);

  const reset = useCallback(() => {
    const socket = socketRef.current;
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: "reset" }));
    }
    setStatus("ready");
    setLastEvent(null);
  }, []);

  const arm = useCallback((sign: string | null, outcome?: string) => {
    const socket = socketRef.current;
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: "arm", sign, outcome }));
    }
  }, []);

  return {
    videoRef,
    cameraState,
    cameraError,
    connected,
    status,
    lastEvent,
    motion,
    isStub,
    vocabularySize,
    startCamera,
    stopCamera,
    reset,
    arm,
  };
}
