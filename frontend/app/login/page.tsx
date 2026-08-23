"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useAuth } from "@/lib/auth";
import { ApiError } from "@/lib/api";

export default function LoginPage() {
  const { signIn } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const user = await signIn(email, password);
      router.push(user.role === "admin" ? "/admin" : "/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not sign in. Please try again.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-dvh flex flex-col items-center justify-center px-4 py-10 bg-page">
      <div className="w-full max-w-[400px]">
        <div className="flex flex-col items-center mb-7">
          <div className="w-12 h-12 rounded-2xl bg-brand flex items-center justify-center mb-3">
            <svg viewBox="0 0 24 24" className="w-6 h-6" fill="none" stroke="white" strokeWidth="2"
                 strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M7 11V6a1.5 1.5 0 0 1 3 0v4" />
              <path d="M10 10V5a1.5 1.5 0 0 1 3 0v5" />
              <path d="M13 10V6.5a1.5 1.5 0 0 1 3 0V13" />
              <path d="M7 11V9a1.5 1.5 0 0 0-3 0v4a8 8 0 0 0 8 8h1a7 7 0 0 0 7-7v-3" />
            </svg>
          </div>
          <h1 className="text-xl font-semibold tracking-tight">PSL Bridge</h1>
          <p className="text-sm text-muted mt-1">Staff sign in</p>
        </div>

        <form onSubmit={submit} className="card p-6 space-y-4">
          <div>
            <label htmlFor="email" className="label">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
              autoFocus
              autoComplete="username"
              placeholder="name@hospital.local"
              className="input"
            />
          </div>

          <div>
            <label htmlFor="password" className="label">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
              autoComplete="current-password"
              className="input"
            />
          </div>

          {error && (
            <p className="text-[13px] text-danger bg-red-50 border border-danger/25 rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          <button type="submit" disabled={busy} className="btn-primary w-full h-12">
            {busy ? "Signing in…" : "Sign in"}
          </button>

          <p className="text-xs text-muted text-center pt-1">
            Accounts are created by an administrator. There is no public sign-up.
          </p>
        </form>

        {/* The patient path must never be behind this form. */}
        <div className="mt-5 card p-4 flex items-start gap-3">
          <svg viewBox="0 0 24 24" className="w-5 h-5 text-brand shrink-0 mt-0.5" fill="none"
               stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
               aria-hidden="true">
            <circle cx="12" cy="12" r="9" />
            <path d="M12 16v-4M12 8h.01" />
          </svg>
          <div className="text-[13px] text-muted">
            <span className="text-ink font-medium">Patients do not need an account.</span>{" "}
            <Link href="/" className="text-brand hover:underline font-medium">
              Open the communication screen
            </Link>{" "}
            and start signing.
          </div>
        </div>
      </div>
    </div>
  );
}
