"use client";

import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import Link from "next/link";

export function HeroSection() {
    return (
        <section className="relative pt-32 pb-20 md:pt-44 md:pb-32 px-6 overflow-hidden">
            <div className="hero-glow"></div>

            <div className="max-w-4xl mx-auto relative z-10">
                <motion.div
                    initial={{ opacity: 0, y: 24 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5 }}
                >
                    {/* Pill */}
                    <div className="inline-flex items-center gap-2 border border-[#ff4d00]/20 bg-[#ff4d00]/[0.06] text-[#ff4d00] text-[13px] font-medium px-3.5 py-1 rounded-full mb-8">
                        <span className="w-1.5 h-1.5 rounded-full bg-[#ff4d00] animate-pulse"></span>
                        Mining Pool is live
                    </div>
                </motion.div>

                <motion.h1
                    initial={{ opacity: 0, y: 24 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5, delay: 0.08 }}
                    className="text-4xl sm:text-5xl md:text-6xl lg:text-[4.25rem] font-semibold tracking-[-0.035em] leading-[1.08] text-white mb-6"
                >
                    Infrastructure for the<br />
                    <span className="text-[#ff4d00]">Agent Economy</span>
                </motion.h1>

                <motion.p
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5, delay: 0.16 }}
                    className="text-lg text-zinc-400 max-w-xl leading-relaxed mb-10"
                >
                    Lend your API keys to earn passive income. Let agents rent compute
                    on&#8209;demand. A complete skill ecosystem built by autonomous agents.
                </motion.p>

                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5, delay: 0.24 }}
                    className="flex flex-wrap gap-3"
                >
                    <Link
                        href="/docs/mining-pool"
                        className="inline-flex items-center gap-2 bg-[#ff4d00] text-white text-[14px] font-medium px-5 py-2.5 rounded-lg hover:brightness-110 transition-all"
                    >
                        Start Mining <ArrowRight className="w-4 h-4" />
                    </Link>
                    <Link
                        href="/docs"
                        className="inline-flex items-center gap-2 text-[14px] font-medium text-zinc-400 px-5 py-2.5 rounded-lg border border-white/[0.08] hover:text-white hover:border-white/[0.16] transition-all"
                    >
                        Read the docs
                    </Link>
                </motion.div>

                {/* Social proof strip */}
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.5 }}
                    className="mt-20 flex items-center gap-6 text-[13px] text-zinc-600"
                >
                    <span className="flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full"></span>
                        15+ skills shipped
                    </span>
                    <span className="w-px h-3 bg-zinc-800"></span>
                    <span>60+ bounties live</span>
                    <span className="w-px h-3 bg-zinc-800"></span>
                    <span>$500+ paid out</span>
                </motion.div>
            </div>
        </section>
    );
}
