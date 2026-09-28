import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RFP Analysis & Response Assistant",
  description: "Evidence-grounded RFP requirement analysis, powered by LangGraph.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">
        <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
          <header className="mb-8 flex items-center justify-between">
            <a href="/" className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-500 text-sm font-bold text-white">
                R
              </div>
              <span className="text-lg font-semibold text-gray-900">
                RFP Analysis &amp; Response Assistant
              </span>
            </a>
            <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800">
              Demo — synthetic data only
            </span>
          </header>
          {children}
        </div>
      </body>
    </html>
  );
}
