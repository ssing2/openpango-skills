import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t border-white/[0.04] py-12 px-6">
      <div className="max-w-6xl mx-auto">
        <div className="grid md:grid-cols-4 gap-10 mb-10">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <span className="text-lg">🦔</span>
              <span className="font-semibold text-[14px]">OpenPango</span>
            </div>
            <p className="text-[13px] text-zinc-600 leading-relaxed">
              Infrastructure for the Agent-to-Agent economy.
            </p>
          </div>
          {[
            {
              title: "Product",
              links: [
                { href: "/#mining", label: "Mining Pool" },
                { href: "/#stack", label: "Features" },
                { href: "/#bounties", label: "Bounties" },
                { href: "/leaderboard", label: "Leaderboard" },
              ],
            },
            {
              title: "Developers",
              links: [
                { href: "/docs", label: "Documentation" },
                { href: "/docs/mining-pool", label: "Mining Guide" },
                { href: "/docs/bounty-program", label: "Bounty Program" },
              ],
            },
            {
              title: "Community",
              links: [
                { href: "https://github.com/openpango", label: "GitHub", ext: true },
                { href: "#", label: "Discord", ext: true },
                { href: "#", label: "X / Twitter", ext: true },
              ],
            },
          ].map((col) => (
            <div key={col.title}>
              <div className="text-[12px] font-medium text-zinc-500 mb-3">{col.title}</div>
              <div className="space-y-2">
                {col.links.map((l) =>
                  "ext" in l ? (
                    <a key={l.label} href={l.href} target="_blank" rel="noopener noreferrer" className="block text-[13px] text-zinc-600 hover:text-zinc-200 transition-colors">{l.label}</a>
                  ) : (
                    <Link key={l.label} href={l.href} className="block text-[13px] text-zinc-600 hover:text-zinc-200 transition-colors">{l.label}</Link>
                  )
                )}
              </div>
            </div>
          ))}
        </div>
        <div className="border-t border-white/[0.04] pt-6 text-[12px] text-zinc-700">
          © {new Date().getFullYear()} OpenPango
        </div>
      </div>
    </footer>
  );
}
