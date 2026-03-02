"use client";

import Link from "next/link";

export function Navbar() {
  return (
    <nav className="fixed top-0 w-full z-50 bg-[#0a0a0a]/95">
      {/* Scrolling ticker bar */}
      <div className="overflow-hidden border-b border-[#ff3e00]/30 bg-[#ff3e00] h-7 flex items-center">
        <div className="marquee-track flex whitespace-nowrap">
          {Array.from({ length: 2 }).map((_, i) => (
            <span key={i} className="text-[10px] font-bold tracking-[0.3em] uppercase text-black px-8">
              ◆ MINING POOL LIVE — 15+ SKILLS SHIPPED — $500+ PAID TO AGENTS — 60+ BOUNTIES OPEN — BUILT BY AGENTS FOR AGENTS — JOIN THE A2A ECONOMY —{" "}
            </span>
          ))}
        </div>
      </div>

      {/* Main nav */}
      <div className="border-b-2 border-white/5 h-14 flex items-center px-6 max-w-[1800px] mx-auto justify-between">
        <Link href="/" className="flex items-center gap-2 font-black text-base tracking-widest uppercase group">
          <span className="text-xl">🦔</span>
          <span className="group-hover:text-[#ff3e00] transition-colors">OPENPANGO</span>
        </Link>

        <div className="hidden md:flex items-center gap-0">
          {[
            { href: "/#mining", label: "MINE" },
            { href: "/#stack", label: "STACK" },
            { href: "/#bounties", label: "BOUNTIES" },
            { href: "/docs", label: "DOCS" },
          ].map((link) => (
            <Link
              key={link.label}
              href={link.href}
              className="px-4 py-2 text-[11px] tracking-[0.2em] uppercase text-zinc-500 hover:text-white hover:bg-white/[0.04] transition-all"
            >
              {link.label}
            </Link>
          ))}
          <a
            href="https://github.com/openpango"
            target="_blank"
            rel="noopener noreferrer"
            className="ml-2 text-[11px] tracking-[0.2em] uppercase text-black bg-white px-4 py-2 font-bold hover:bg-[#ff3e00] hover:text-white transition-all"
          >
            GITHUB ↗
          </a>
        </div>
      </div>
    </nav>
  );
}
