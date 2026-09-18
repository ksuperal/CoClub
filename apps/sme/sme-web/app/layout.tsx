import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CoClub",
  description: "AI marketing pipeline for SMEs",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        <div className="max-w-3xl mx-auto px-4 py-8">{children}</div>
      </body>
    </html>
  );
}
