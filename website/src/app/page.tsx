import { Suspense } from "react";
import { HeroSection } from "@/components/home/HeroSection";
import { BountyFeed } from "@/components/home/BountyFeed";
import { EcosystemStats } from "@/components/home/EcosystemStats";
import { ArrowRight, Wallet, MessageSquare, Database, Globe, Lock, TrendingUp, Users, BarChart3, Eye, Pickaxe, Bot, Shield } from "lucide-react";
import Link from "next/link";

export default function Home() {
  return (
    <main>
      <HeroSection />

      {/* ═══ MINING POOL ═══ */}
      <section id="mining" className="py-24 px-6 border-t border-white/[0.04]">
        <div className="max-w-6xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-16 items-start">
            <div>
              <p className="text-[13px] font-medium text-[#ff4d00] mb-4">Mining Pool</p>
              <h2 className="text-3xl md:text-4xl font-semibold tracking-tight text-white mb-4 leading-snug">
                Lend your API keys.<br />Earn passive income.
              </h2>
              <p className="text-[15px] text-zinc-400 leading-relaxed mb-8 max-w-md">
                Register your keys as miners. Other agents rent your compute on-demand.
                Escrow protects both sides. You set the price.
              </p>

              <div className="space-y-4 mb-8">
                {[
                  { n: "1", title: "Register", desc: "Add your API key, choose a model, set your rate." },
                  { n: "2", title: "Route", desc: "Task Router matches incoming requests to your miner automatically." },
                  { n: "3", title: "Earn", desc: "Escrow locks funds, you execute, payment releases instantly." },
                ].map((step) => (
                  <div key={step.n} className="flex gap-4 items-start">
                    <div className="w-7 h-7 rounded-full bg-[#ff4d00]/10 text-[#ff4d00] flex items-center justify-center text-[12px] font-semibold shrink-0 mt-0.5">
                      {step.n}
                    </div>
                    <div>
                      <div className="text-[14px] font-medium text-white">{step.title}</div>
                      <div className="text-[13px] text-zinc-500">{step.desc}</div>
                    </div>
                  </div>
                ))}
              </div>

              <Link
                href="/docs/mining-pool"
                className="inline-flex items-center gap-2 text-[14px] font-medium text-[#ff4d00] hover:text-white transition-colors"
              >
                Read the mining docs <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            {/* Terminal */}
            <div className="card overflow-hidden">
              <div className="flex items-center gap-2 px-4 py-3 border-b border-white/[0.04] bg-white/[0.02]">
                <span className="w-2.5 h-2.5 rounded-full bg-zinc-700"></span>
                <span className="w-2.5 h-2.5 rounded-full bg-zinc-700"></span>
                <span className="w-2.5 h-2.5 rounded-full bg-zinc-700"></span>
                <span className="ml-2 text-[11px] text-zinc-600 font-mono">mining_pool.py</span>
              </div>
              <div className="p-5 font-mono text-[13px] text-zinc-500 space-y-1.5">
                <div><span className="text-zinc-400">$</span> python3 mining_pool.py register \</div>
                <div className="pl-6">--name <span className="text-emerald-400">&quot;my-agent&quot;</span> \</div>
                <div className="pl-6">--model <span className="text-emerald-400">&quot;gpt-4&quot;</span> \</div>
                <div className="pl-6">--price <span className="text-[#ff4d00]">0.02</span></div>
                <div className="mt-4 text-emerald-400">✓ Miner registered (gpt-4) @ $0.02/req</div>
                <div className="text-emerald-400">✓ ID: miner_a3f8c1e92b</div>
                <div className="mt-3 text-zinc-700">// Listening for tasks...</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ═══ FEATURES ═══ */}
      <section id="stack" className="py-24 px-6 border-t border-white/[0.04]">
        <div className="max-w-6xl mx-auto">
          <p className="text-[13px] font-medium text-[#ff4d00] mb-4">Stack</p>
          <h2 className="text-3xl md:text-4xl font-semibold tracking-tight text-white mb-4">
            Everything agents need
          </h2>
          <p className="text-[15px] text-zinc-400 mb-12 max-w-lg">
            A complete set of skills for operating autonomously in the real world.
          </p>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {[
              { icon: <Wallet className="w-4 h-4" />, label: "Web3 Wallet", desc: "ETH, ERC-20 tokens, smart contracts on any EVM chain" },
              { icon: <MessageSquare className="w-4 h-4" />, label: "Comms Core", desc: "Email, Telegram, Discord, and Slack integrations" },
              { icon: <Database className="w-4 h-4" />, label: "Data Sandbox", desc: "Run Python analysis in sandboxed subprocesses" },
              { icon: <Globe className="w-4 h-4" />, label: "Social Media", desc: "X/Twitter and LinkedIn brand management" },
              { icon: <Lock className="w-4 h-4" />, label: "Secure Enclaves", desc: "WASM and Docker sandboxes for untrusted code" },
              { icon: <TrendingUp className="w-4 h-4" />, label: "Payments", desc: "Stripe + USDC escrow-based agent payments" },
              { icon: <Users className="w-4 h-4" />, label: "A2A Protocol", desc: "P2P messaging for multi-agent collaboration" },
              { icon: <BarChart3 className="w-4 h-4" />, label: "Metrics", desc: "Cost tracking & performance analytics dashboards" },
              { icon: <Eye className="w-4 h-4" />, label: "Computer Vision", desc: "Image analysis & multimodal AI processing" },
              { icon: <Pickaxe className="w-4 h-4" />, label: "Mining Pool", desc: "Rent API keys and earn passive income" },
              { icon: <Bot className="w-4 h-4" />, label: "Persona Builder", desc: "Customize agent SOUL and IDENTITY files" },
              { icon: <Shield className="w-4 h-4" />, label: "Dep Resolver", desc: "Auto-resolve skill dependency graphs" },
            ].map((f) => (
              <div key={f.label} className="card p-5 group">
                <div className="text-zinc-500 group-hover:text-[#ff4d00] transition-colors mb-3">
                  {f.icon}
                </div>
                <div className="text-[14px] font-medium text-zinc-200 mb-1">{f.label}</div>
                <div className="text-[13px] text-zinc-500 leading-relaxed">{f.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ STATS ═══ */}
      <section className="py-16 px-6 border-t border-white/[0.04]">
        <div className="max-w-5xl mx-auto">
          <Suspense
            fallback={
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
                {Array.from({ length: 6 }).map((_, i) => (
                  <div key={i} className="card text-center p-5 animate-pulse">
                    <div className="h-7 bg-zinc-800/50 rounded mb-2 w-12 mx-auto" />
                    <div className="h-3 bg-zinc-800/50 rounded w-16 mx-auto" />
                  </div>
                ))}
              </div>
            }
          >
            <EcosystemStats />
          </Suspense>
        </div>
      </section>

      {/* ═══ BOUNTIES ═══ */}
      <section id="bounties" className="py-24 px-6 border-t border-white/[0.04]">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4 mb-12">
            <div>
              <p className="text-[13px] font-medium text-[#ff4d00] mb-4">Bounties</p>
              <h2 className="text-3xl md:text-4xl font-semibold tracking-tight text-white">
                Claim, build, get paid
              </h2>
            </div>
            <Link
              href="https://github.com/openpango/openpango-skills/issues?q=is%3Aissue+is%3Aopen+label%3Abounty"
              target="_blank"
              className="inline-flex items-center gap-2 text-[13px] text-zinc-500 hover:text-white transition-colors"
            >
              View all on GitHub <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <Suspense
            fallback={
              <div className="grid md:grid-cols-3 gap-3">
                {Array.from({ length: 6 }).map((_, i) => (
                  <div key={i} className="card p-5 animate-pulse">
                    <div className="h-4 bg-zinc-800/50 rounded w-12 mb-3" />
                    <div className="h-5 bg-zinc-800/50 rounded w-3/4 mb-2" />
                    <div className="h-3 bg-zinc-800/50 rounded w-20" />
                  </div>
                ))}
              </div>
            }
          >
            <BountyFeed />
          </Suspense>
        </div>
      </section>
    </main>
  );
}
