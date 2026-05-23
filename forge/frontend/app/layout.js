import Link from "next/link";
import "./globals.css";

export const metadata = {
  title: "Forge Dashboard",
  description: "AI Experimentation Sandbox",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className="h-full">
      <body className="min-h-full flex flex-col bg-zinc-50 text-zinc-900">
        <header className="border-b border-zinc-200 bg-white px-6 py-3 flex items-center gap-6">
          <Link href="/" className="text-lg font-bold tracking-tight">
            ⚒️ Forge
          </Link>
          <nav className="flex gap-4 text-sm text-zinc-500">
            <Link href="/" className="hover:text-zinc-900 transition-colors">Experiments</Link>
          </nav>
        </header>
        <main className="flex-1 p-6">{children}</main>
      </body>
    </html>
  );
}
