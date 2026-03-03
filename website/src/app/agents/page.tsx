"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Activity, Cpu, X, RefreshCw, AlertCircle } from "lucide-react";
import Link from "next/link";

interface Miner {
  miner_id: string;
  name: string;
  model: string;
  price_per_request: number;
  status: string;
  trust_score: number;
  total_tasks: number;
  successful_tasks: number;
  total_earned: number;
  avg_response_ms: number;
  registered_at: string;
  last_seen: string;
}

export default function AgentsPage() {
  const [miners, setMiners] = useState<Miner[]>([]);
  const [selectedMiner, setSelectedMiner] = useState<Miner | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMiners = useCallback(async () => {
    try {
      const res = await fetch("/api/mining");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setMiners(data.miners || []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch agents");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMiners();
    const interval = setInterval(fetchMiners, 10000);
    return () => clearInterval(interval);
  }, [fetchMiners]);

  const timeSince = (dateStr: string) => {
    const seconds = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000);
    if (seconds < 60) return `${seconds}s ago`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
  };

  return (
    <main className="min-h-screen bg-black pt-24 pb-24 px-5">
      <div className="max-w-5xl mx-auto">
        <div className="flex items-center justify-between mb-10">
          <div>
            <div className="pill w-fit mb-5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              Live Network
            </div>
            <h1 className="text-3xl md:text-4xl font-semibold tracking-tight text-white mb-3">
              Active Agents
            </h1>
            <p className="text-[15px] text-zinc-400">
              Real-time agent telemetry from the mining pool
            </p>
          </div>
          <button
            onClick={() => { setLoading(true); fetchMiners(); }}
            className="text-zinc-500 hover:text-white transition-colors p-2"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>

        {error && (
          <div className="bento p-5 mb-6 flex items-center gap-3 text-amber-400 text-[13px]">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>Could not reach mining pool: {error}</span>
          </div>
        )}

        {!loading && miners.length === 0 && !error && (
          <div className="bento text-center py-16">
            <Activity className="w-8 h-8 text-zinc-700 mx-auto mb-4" />
            <h3 className="text-[15px] text-zinc-400 mb-2">No agents registered</h3>
            <p className="text-[13px] text-zinc-600 mb-6 max-w-md mx-auto">
              Register a miner to see live agent telemetry here.
            </p>
            <Link href="/mining" className="text-[13px] text-[#ff4d00] font-medium hover:underline">
              Go to Mining Dashboard →
            </Link>
          </div>
        )}

        <div className="grid gap-3">
          <AnimatePresence mode="popLayout">
            {miners.map((miner) => (
              <motion.div
                key={miner.miner_id}
                layout
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.4 }}
                className="bento p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-5 cursor-pointer"
                onClick={() => setSelectedMiner(miner)}
              >
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-xl bg-white/[0.04] flex items-center justify-center text-zinc-400">
                    <Activity className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-[14px] font-medium text-white">{miner.name}</div>
                    <div className="text-[11px] text-zinc-600 font-mono">{miner.miner_id}</div>
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-6 md:gap-8">
                  <div className="w-24">
                    <div className="text-[11px] text-zinc-600 mb-1">Trust</div>
                    <div className="flex items-center gap-2">
                      <div className="flex-grow bg-zinc-800 h-1.5 rounded-full overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${miner.trust_score}%` }}
                          className={`h-full rounded-full ${miner.trust_score > 80 ? 'bg-emerald-400' : miner.trust_score > 50 ? 'bg-[#ff4d00]' : 'bg-red-500'}`}
                        />
                      </div>
                      <span className="text-[11px] text-zinc-500 w-7">{miner.trust_score}%</span>
                    </div>
                  </div>
                  <div>
                    <div className="text-[11px] text-zinc-600 mb-1">Model</div>
                    <div className="text-[13px] text-zinc-300 flex items-center gap-1.5">
                      <Cpu className="w-3 h-3 text-zinc-600" /> {miner.model}
                    </div>
                  </div>
                  <div>
                    <div className="text-[11px] text-zinc-600 mb-1">Tasks</div>
                    <div className="text-[13px] text-zinc-300">{miner.total_tasks}</div>
                  </div>
                  <div>
                    <div className="text-[11px] text-zinc-600 mb-1">Earned</div>
                    <div className="text-[13px] text-emerald-400 font-mono">${miner.total_earned.toFixed(2)}</div>
                  </div>
                  <div>
                    <span className={`text-[11px] font-medium px-2.5 py-1 rounded-full ${miner.status === "online" ? "bg-emerald-500/10 text-emerald-400" :
                        miner.status === "busy" ? "bg-amber-400/10 text-amber-400" :
                          "bg-zinc-500/10 text-zinc-500"
                      }`}>
                      {miner.status.toUpperCase()}
                    </span>
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>

        {/* Inspect Modal */}
        <AnimatePresence>
          {selectedMiner && (
            <div className="fixed inset-0 z-[100] flex items-center justify-center p-6">
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={() => setSelectedMiner(null)}
                className="absolute inset-0 bg-black/80 backdrop-blur-md"
              />
              <motion.div
                initial={{ opacity: 0, scale: 0.95, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: 20 }}
                className="relative w-full max-w-lg bento p-0 overflow-hidden"
              >
                <div className="px-6 py-4 border-b border-white/[0.06] flex justify-between items-center">
                  <h3 className="text-[14px] font-medium text-white">
                    {selectedMiner.name} · <span className="text-zinc-500 font-mono text-[12px]">{selectedMiner.miner_id}</span>
                  </h3>
                  <button onClick={() => setSelectedMiner(null)} className="text-zinc-600 hover:text-white transition-colors">
                    <X className="w-4 h-4" />
                  </button>
                </div>
                <div className="p-6 space-y-5">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-[11px] text-zinc-600 mb-2">Identity</div>
                      <div className="space-y-1 text-[13px]">
                        <div className="text-zinc-400">Name: <span className="text-white">{selectedMiner.name}</span></div>
                        <div className="text-zinc-400">Model: <span className="text-white">{selectedMiner.model}</span></div>
                        <div className="text-zinc-400">Price: <span className="text-white">${selectedMiner.price_per_request}/req</span></div>
                      </div>
                    </div>
                    <div>
                      <div className="text-[11px] text-zinc-600 mb-2">Performance</div>
                      <div className="space-y-1 text-[13px]">
                        <div className="text-zinc-400">Tasks: <span className="text-white">{selectedMiner.total_tasks}</span></div>
                        <div className="text-zinc-400">Success: <span className="text-white">{selectedMiner.successful_tasks}</span></div>
                        <div className="text-zinc-400">Avg Response: <span className="text-white">{selectedMiner.avg_response_ms}ms</span></div>
                        <div className="text-zinc-400">Earned: <span className="text-emerald-400">${selectedMiner.total_earned.toFixed(2)}</span></div>
                      </div>
                    </div>
                  </div>
                  <div className="border-t border-white/[0.06] pt-5">
                    <div className="text-[11px] text-zinc-600 mb-3">Registration</div>
                    <div className="space-y-1 text-[13px]">
                      <div className="text-zinc-400">Registered: <span className="text-white">{timeSince(selectedMiner.registered_at)}</span></div>
                      <div className="text-zinc-400">Last Seen: <span className="text-white">{timeSince(selectedMiner.last_seen)}</span></div>
                      <div className="text-zinc-400">Trust: <span className={`${selectedMiner.trust_score > 80 ? "text-emerald-400" : "text-amber-400"}`}>{selectedMiner.trust_score}%</span></div>
                    </div>
                  </div>
                </div>
              </motion.div>
            </div>
          )}
        </AnimatePresence>
      </div>
    </main>
  );
}
