"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/lib/auth";

const NAV = [
  { href: "/admin", label: "Dashboard", exact: true, icon: "M3 12h7V3H3v9Zm11 9h7v-9h-7v9ZM3 21h7v-6H3v6Zm11-12h7V3h-7v6Z" },
  { href: "/admin/signs", label: "Signs", icon: "M9 11V6a1.5 1.5 0 0 1 3 0v5M12 10V5.5a1.5 1.5 0 0 1 3 0V11M9 11V9a1.5 1.5 0 0 0-3 0v4a8 8 0 0 0 8 8 7 7 0 0 0 7-7v-4a1.5 1.5 0 0 0-3 0" },
  { href: "/admin/messages", label: "Patient messages", icon: "M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v10Z" },
  { href: "/admin/doctor-phrases", label: "Doctor phrases", icon: "M6 3v6a6 6 0 0 0 12 0V3M6 3H4M18 3h2M12 15v2a4 4 0 0 0 8 0v-1" },
  { href: "/admin/record", label: "Record signs", icon: "M12 15a3 3 0 0 0 3-3V6a3 3 0 0 0-6 0v6a3 3 0 0 0 3 3ZM19 10v2a7 7 0 0 1-14 0v-2M12 19v3" },
  { href: "/admin/live-test", label: "Live test", icon: "M23 7l-7 5 7 5V7zM1 5h15v14H1zM8 9v6l4-3-4-3Z" },
  { href: "/admin/testing", label: "Testing", icon: "M9 3v6l-6 9a2 2 0 0 0 1.7 3h14.6a2 2 0 0 0 1.7-3l-6-9V3M8 3h8" },
  { href: "/admin/assets", label: "Assets & rights", icon: "M4 4h16v12H4zM2 20h20M9 8l4 3-4 3V8Z" },
  { href: "/admin/users", label: "Users", icon: "M16 21v-2a4 4 0 0 0-8 0v2M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z" },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  // The server rejects non-admins on every endpoint regardless; this is only
  // so the UI does not show an empty shell.
  useEffect(() => {
    if (!loading && (!user || user.role !== "admin")) router.replace("/login");
  }, [loading, user, router]);

  if (loading || !user || user.role !== "admin") {
    return (
      <div className="min-h-dvh grid place-items-center text-muted text-sm">
        {loading ? "Loading…" : "Administrator access required. Redirecting…"}
      </div>
    );
  }

  return (
    <div className="min-h-dvh flex bg-page">
      <aside className="w-60 shrink-0 bg-surface border-r border-line flex flex-col sticky top-0 h-dvh">
        <div className="h-16 flex items-center gap-2.5 px-5 border-b border-line">
          <div className="w-8 h-8 rounded-lg bg-brand flex items-center justify-center">
            <svg viewBox="0 0 24 24" className="w-4 h-4" fill="none" stroke="white" strokeWidth="2.2"
                 strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M7 11V6a1.5 1.5 0 0 1 3 0v4M10 10V5a1.5 1.5 0 0 1 3 0v5" />
              <path d="M13 10V6.5a1.5 1.5 0 0 1 3 0V13M7 11V9a1.5 1.5 0 0 0-3 0v4a8 8 0 0 0 8 8h1a7 7 0 0 0 7-7v-3" />
            </svg>
          </div>
          <div className="leading-tight">
            <div className="font-semibold text-sm">Ishara AI</div>
            <div className="text-[11px] text-muted -mt-0.5">Admin console</div>
          </div>
        </div>

        <nav className="flex-1 p-3 space-y-0.5">
          {NAV.map((item) => {
            const active = item.exact ? pathname === item.href : pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-2.5 px-3 h-10 rounded-lg text-sm transition-colors ${
                  active
                    ? "bg-brand-soft text-brand font-medium"
                    : "text-muted hover:bg-page hover:text-ink"
                }`}
              >
                <svg viewBox="0 0 24 24" className="w-4 h-4 shrink-0" fill="none"
                     stroke="currentColor" strokeWidth="1.9" strokeLinecap="round"
                     strokeLinejoin="round" aria-hidden="true">
                  <path d={item.icon} />
                </svg>
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="p-3 border-t border-line space-y-0.5">
          <Link href="/settings"
                className="flex items-center gap-2.5 px-3 h-10 rounded-lg text-sm text-muted hover:bg-page hover:text-ink">
            <svg viewBox="0 0 24 24" className="w-4 h-4" fill="none" stroke="currentColor"
                 strokeWidth="1.9" strokeLinecap="round" aria-hidden="true">
              <circle cx="12" cy="12" r="3" />
              <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-2.9 1.2 2 2 0 1 1-4 0 1.7 1.7 0 0 0-2.9-1.2l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1A1.7 1.7 0 0 0 3 15a2 2 0 1 1 0-4 1.7 1.7 0 0 0 1.2-2.9l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1A1.7 1.7 0 0 0 10 4a2 2 0 1 1 4 0 1.7 1.7 0 0 0 2.9 1.2l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1A1.7 1.7 0 0 0 21 11a2 2 0 1 1 0 4Z" />
            </svg>
            Settings
          </Link>
          <Link href="/"
                className="flex items-center gap-2.5 px-3 h-10 rounded-lg text-sm text-muted hover:bg-page hover:text-ink">
            <svg viewBox="0 0 24 24" className="w-4 h-4" fill="none" stroke="currentColor"
                 strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="m19 12-7-7-7 7M19 12H5M19 12v7H5v-7" />
            </svg>
            Communication screen
          </Link>
        </div>
      </aside>

      <main className="flex-1 min-w-0">{children}</main>
    </div>
  );
}
