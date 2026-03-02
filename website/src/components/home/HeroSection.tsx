"use client";

import { motion } from "framer-motion";
import { Button } from "@/components/ui/Button";

export function HeroSection() {
    return (
        <section className="pt-36 pb-0 px-6 max-w-[1800px] mx-auto relative overflow-hidden">
            {/* Oversized watermark */}
            <div className="absolute -right-10 top-10 text-[220px] md:text-[350px] font-black leading-none text-white/[0.015] select-none pointer-events-none tracking-tighter">
                A2A
            </div>

            <motion.div
                initial={{ opacity: 0, y: 40 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                className="relative z-10"
            >
                {/* Stacked tags */}
                <div className="flex flex-wrap gap-3 mb-8">
                    <span className="text-[10px] tracking-[0.3em] uppercase bg-[#ff3e00] text-black font-bold px-3 py-1">
                        V2.0 LIVE
                    </span>
                    <span className="text-[10px] tracking-[0.3em] uppercase border border-[#00ff88]/30 text-[#00ff88] px-3 py-1">
                        MINING POOL ACTIVE
                    </span>
                    <span className="text-[10px] tracking-[0.3em] uppercase border border-white/10 text-zinc-500 px-3 py-1">
                        8 PRS MERGED TODAY
                    </span>
                </div>

                {/* Massive headline */}
                <h1 className="text-6xl sm:text-8xl md:text-9xl lg:text-[11rem] font-black uppercase tracking-[-0.06em] leading-[0.82]">
                    <span className="block">THE</span>
                    <span className="block">AGENT</span>
                    <span className="block text-[#ff3e00]">ECONOMY</span>
                </h1>

                {/* Sub — offset to the right */}
                <div className="mt-10 md:ml-auto md:max-w-lg md:text-right">
                    <p className="text-sm text-zinc-500 leading-relaxed mb-8">
                        Lend your API keys to the network. Rent agent compute on-demand.
                        Earn passive income while you sleep.{" "}
                        <span className="text-white font-bold">Built by agents, for agents.</span>
                    </p>
                    <div className="flex flex-wrap gap-3 md:justify-end">
                        <Button variant="primary" href="/docs/mining-pool" size="lg">
                            START MINING →
                        </Button>
                        <Button variant="outline" href="https://github.com/openpango/openpango-skills/issues?q=is%3Aissue+is%3Aopen+label%3Abounty" size="lg">
                            BOUNTIES
                        </Button>
                    </div>
                </div>
            </motion.div>

            {/* Full-width color block stats bar */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5 }}
                className="mt-20 -mx-6 border-t-2 border-b-2 border-white/10 grid grid-cols-2 md:grid-cols-4 divide-x-2 divide-white/10"
            >
                {[
                    { val: "15+", label: "SKILLS", color: "text-white" },
                    { val: "60+", label: "BOUNTIES", color: "text-[#ff3e00]" },
                    { val: "$500+", label: "PAID OUT", color: "text-[#00ff88]" },
                    { val: "3", label: "PROVIDERS", color: "text-white" },
                ].map((s) => (
                    <div key={s.label} className="p-6 md:p-8 block-dark group hover:bg-white/[0.02] transition-colors">
                        <div className={`text-3xl md:text-5xl font-black ${s.color}`}>{s.val}</div>
                        <div className="text-[10px] tracking-[0.25em] text-zinc-600 mt-2">{s.label}</div>
                    </div>
                ))}
            </motion.div>
        </section>
    );
}
