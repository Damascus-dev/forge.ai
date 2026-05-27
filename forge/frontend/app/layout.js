"use client";

import Link from "next/link";
import { useState, useEffect } from "react";
import "./globals.css";

export const metadata = {
  title: "Forge Dashboard",
  description: "AI Experimentation Sandbox",
};

export default function RootLayout({ children }) {
  const [apiKey, setApiKey] = useState("");
  const [showKeyInput, setShowKeyInput] = useState(false);

  useEffect(() => {
    setApiKey(localStorage.getItem("forge_api_key") || "");
  }, []);

  function handleKeySave(e) {
    e.preventDefault();
    localStorage.setItem("forge_api_key", apiKey);
    setShowKeyInput(false);
  }

  function handleKeyClear() {
    localStorage.removeItem("forge_api_key");
    setApiKey("");
    setShowKeyInput(false);
  }

  return (
    <html lang="en" className="h-full">
      <body className="min-h-full flex flex-col bg-zinc-50 text-zinc-900">
        <header className="border-b border-zinc-200 bg-white px-6 py-3 flex items-center gap-6">
          <Link href="/" className="text-lg font-bold tracking-tight">
            ⚒️ Forge
          </Link>
          <nav className="flex gap-4 text-sm text-zinc-500 flex-1">
            <Link href="/" className="hover:text-zinc-900 transition-colors">Experiments</Link>
          </nav>
          <div className="relative">
            <button
              onClick={() => setShowKeyInput(!showKeyInput)}
              className={`text-xs px-2 py-1 rounded border font-medium transition-colors ${
                apiKey
                  ? "text-green-600 bg-green-50 border-green-200"
                  : "text-zinc-400 bg-zinc-50 border-zinc-200"
              }`}
              title={apiKey ? "API key set" : "No API key"}
            >
              {apiKey ? "🔑" : "🔓"}
            </button>
            {showKeyInput && (
              <form onSubmit={handleKeySave} className="absolute right-0 top-8 w-72 p-3 bg-white border border-zinc-200 rounded-lg shadow-lg z-50">
                <label className="block text-xs font-medium text-zinc-500 mb-1">API Key (X-API-Key)</label>
                <input
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  className="w-full px-2 py-1.5 border border-zinc-200 rounded text-sm mb-2 focus:outline-none focus:ring-2 focus:ring-zinc-400"
                  placeholder="Enter API key..."
                />
                <div className="flex gap-2">
                  <button type="submit" className="px-3 py-1 bg-zinc-900 text-white rounded text-xs font-medium hover:bg-zinc-800">
                    Save
                  </button>
                  {apiKey && (
                    <button type="button" onClick={handleKeyClear} className="px-3 py-1 text-zinc-500 rounded text-xs hover:text-zinc-700">
                      Clear
                    </button>
                  )}
                </div>
              </form>
            )}
          </div>
        </header>
        <main className="flex-1 p-6">{children}</main>
      </body>
    </html>
  );
}
