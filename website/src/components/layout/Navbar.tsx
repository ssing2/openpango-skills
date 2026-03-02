"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const navLinks = [
  { href: "/#mining", label: "Mining" },
  { href: "/#stack", label: "Stack" },
  { href: "/#bounties", label: "Bounties" },
  { href: "/docs", label: "Docs" },
  { href: "/leaderboard", label: "Leaderboard" },
];

export function Navbar() {
  const pathname = usePathname();

  return (
    <nav className="fixed top-0 w-full z-50 border-b border-white/[0.06] bg-[#09090b]/80 backdrop-blur-lg">
      <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2.5 group">
          <span className="text-xl">🦔</span>
          <span className="font-semibold text-[15px] tracking-tight group-hover:text-[#ff4d00] transition-colors">
            OpenPango
          </span>
        </Link>

        <div className="hidden md:flex items-center gap-1">
          {navLinks.map((link) => (
            <Link
              key={link.label}
              href={link.href}
              className={cn(
                "px-3 py-1.5 text-[13px] rounded-md transition-colors",
                pathname === link.href
                  ? "text-white bg-white/[0.06]"
                  : "text-zinc-500 hover:text-zinc-200"
              )}
            >
              {link.label}
            </Link>
          ))}
        </div>

        <a
          href="https://github.com/openpango"
          target="_blank"
          rel="noopener noreferrer"
          className="hidden md:inline-flex items-center gap-2 text-[13px] text-zinc-500 hover:text-white px-3 py-1.5 rounded-md border border-white/[0.08] hover:border-white/[0.15] transition-all"
        >
          GitHub
          <svg className="w-3 h-3" fill="none" viewBox="0 0 12 12"><path d="M2 10L10 2M10 2H4M10 2V8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" /></svg>
        </a>
      </div>
    </nav>
  );
}
