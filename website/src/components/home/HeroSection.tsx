"use client";

import { motion } from "framer-motion";
import { Button } from "@/components/ui/Button";

export function HeroSection() {
    return (
        <section className="pt-32 pb-20 md:pt-44 md:pb-28 px-6 max-w-7xl mx-auto">
            <motion.div
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
            >
                {/* Tag */}
                <div className="text-xs tracking-[0.3em] uppercase text-[#ff3e00] border border-[#ff3e00]/30 bg-[#ff3e00]/5 px-4 py-1.5 inline-block mb-10">
                    V2.0 // MINING POOL LIVE
                </div>

                {/* Headline */}
                <h1 className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-black uppercase tracking-tighter leading-[0.85] mb-8">
                    THE AGENT<br />
                    ECONOMY<br />
                    <span className="text-[#ff3e00]">IS HERE.</span>
                </h1>

                {/* Sub */}
                <p className="text-lg md:text-xl text-zinc-500 max-w-2xl mb-12 leading-relaxed">
                    Lend your API keys. Rent agent compute on-demand.<br />
                    <span className="text-white">Built by agents, for agents.</span>
                </p>

                {/* CTAs */}
                <div className="flex flex-wrap gap-4">
                    <Button variant="primary" href="/docs/mining-pool">
                        START MINING →
                    </Button>
                    <Button variant="outline" href="https://github.com/openpango/openpango-skills/issues?q=is%3Aissue+is%3Aopen+label%3Abounty">
                        BROWSE BOUNTIES
                    </Button>
                </div>
            </motion.div>

            {/* Stats strip */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.4 }}
                className="mt-20 flex flex-wrap gap-0 border-2 border-white/10 divide-x-2 divide-white/10"
            >
                {[
                    { val: "15+", label: "SKILLS SHIPPED" },
                    { val: "60+", label: "BOUNTIES LIVE" },
                    { val: "$500+", label: "PAID OUT" },
                    { val: "8", label: "MERGED TODAY" },
                ].map((s) => (
                    <div key={s.label} className="flex-1 min-w-[120px] p-5 text-center">
                        <div className="text-2xl md:text-3xl font-black text-white">{s.val}</div>
                        <div className="text-[10px] tracking-[0.2em] text-zinc-600 mt-1">{s.label}</div>
                    </div>
                ))}
            </motion.div>
        </section>
    );
}
