import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Gnani Audio Notes",
  description: "Upload audio, get transcripts and AI summaries powered by Gnani ASR",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-gray-50 text-gray-900 min-h-screen">
        <nav className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <span className="font-semibold text-lg tracking-tight">🎙 Gnani Audio Notes</span>
          <a
            href="/architecture"
            className="text-sm text-blue-600 hover:underline"
          >
            Architecture
          </a>
        </nav>
        <main className="max-w-4xl mx-auto px-4 py-8">{children}</main>
      </body>
    </html>
  );
}
