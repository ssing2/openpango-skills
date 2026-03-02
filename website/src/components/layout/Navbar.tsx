"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

export function Navbar() {
  const pathname = usePathname();

  const navLinks = [
    { href: "/#mining", label: "MINING" },
    { href: "/#stack", label: "STACK" },
    { href: "/#bounties", label: "BOUNTIES" },
    { href: "/docs", label: "DOCS" },
    { href: "/leaderboard", label: "BOARD" },
  ];

  return (
    <nav className="fixed top-0 w-full z-50 border-b-2 border-white/10 bg-black/90 backdrop-blur-sm">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 text-lg font-bold tracking-widest uppercase hover:text-[#ff3e00] transition-colors">
          <span className="text-2xl">🦔</span> OPENPANGO
        </Link>

        <div className="hidden md:flex items-center gap-1">
          {navLinks.map((link) => {
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.label}
                href={link.href}
                className={cn(
                  "px-3 py-1.5 text-xs tracking-widest uppercase transition-colors",
                  isActive
                    ? "text-[#ff3e00] border-b-2 border-[#ff3e00]"
                    : "text-zinc-500 hover:text-white"
                )}
              >
                {link.label}
              </Link>
            );
          })}
          <span className="mx-3 text-zinc-700">|</span>
          <a
            href="https://github.com/openpango"
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs tracking-widest uppercase text-zinc-500 hover:text-white border border-zinc-700 px-3 py-1.5 hover:border-[#ff3e00] transition-colors"
          >
            GITHUB ↗
          </a>
        </div>
      </div>
    </nav>
  );
}
