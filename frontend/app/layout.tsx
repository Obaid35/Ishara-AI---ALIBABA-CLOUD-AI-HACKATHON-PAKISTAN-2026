import type { Metadata, Viewport } from "next";
import { Inter, Noto_Sans_Arabic } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/lib/auth";

// A clean sans with strong Urdu support — decorative Nastaliq faces are
// deliberately avoided (docs/DESIGN_SYSTEM.md).
const ui = Inter({ subsets: ["latin"], variable: "--font-ui", display: "swap" });
const urdu = Noto_Sans_Arabic({
  subsets: ["arabic"],
  variable: "--font-urdu",
  display: "swap",
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "Ishara AI",
  description:
    "Healthcare communication between Pakistan Sign Language users and Urdu-speaking " +
    "medical staff. Communication assistance only — not diagnostic.",
};

export const viewport: Viewport = {
  themeColor: "#017A3A",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${ui.variable} ${urdu.variable}`}>
      <body>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
