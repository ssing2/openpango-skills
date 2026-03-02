import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t-2 border-white/10 bg-black relative z-10">
      <div className="max-w-7xl mx-auto px-6 py-10 flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="flex items-center gap-2 text-sm font-bold tracking-widest uppercase">
          <span className="text-xl">🦔</span> OPENPANGO
        </div>
        <div className="flex flex-wrap gap-6 text-xs tracking-[0.2em] uppercase text-zinc-600">
          <Link href="/docs" className="hover:text-[#ff3e00] transition-colors">DOCS</Link>
          <a href="https://github.com/openpango" target="_blank" rel="noopener noreferrer" className="hover:text-[#ff3e00] transition-colors">GITHUB</a>
          <Link href="/docs/mining-pool" className="hover:text-[#ff3e00] transition-colors">MINING</Link>
          <Link href="/leaderboard" className="hover:text-[#ff3e00] transition-colors">LEADERBOARD</Link>
        </div>
        <div className="text-[10px] tracking-[0.2em] text-zinc-700 uppercase">
          &copy; {new Date().getFullYear()} ALL SYSTEMS NOMINAL
        </div>
      </div>
    </footer>
  );
}
