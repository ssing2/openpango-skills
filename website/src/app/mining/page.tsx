"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Pickaxe, TrendingUp, Zap, Clock, Users, ArrowRight, RefreshCw, AlertCircle } from "lucide-react";
import Link from "next/link";
import { getAdminKey, clearAdminKey } from "@/lib/auth";

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

interface PoolStats {
    total_miners: number;
    online_miners: number;
    total_tasks_processed: number;
    total_revenue: number;
    available_models: string[];
}

interface TaskActivity {
    task_id: string;
    miner_id: string;
    miner_name: string;
    model: string;
    status: string;
    cost: number;
    response_ms: number;
    created_at: string;
    completed_at: string | null;
}

export default function MiningDashboard() {
    const [miners, setMiners] = useState<Miner[]>([]);
    const [stats, setStats] = useState<PoolStats | null>(null);
    const [activity, setActivity] = useState<TaskActivity[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

    const fetchData = useCallback(async () => {
        try {
            // Fetch sequentially to prevent SQLite database lock collisions
            // when multiple Python scripts try to instantiate the MiningPool simultaneously.
            const statsRes = await fetch("/api/mining?cmd=stats");
            const actRes = await fetch("/api/mining?cmd=activity");

            if (!statsRes.ok || !actRes.ok) throw new Error("Failed to fetch mining data");

            const statsData = await statsRes.json();
            const actData = await actRes.json();

            if (statsData.error) throw new Error(statsData.error);

            setStats(statsData.stats);
            setMiners(statsData.miners || []);
            setActivity(actData.activity || []);
            setError(null);
            setLastRefresh(new Date());
        } catch (err) {
            setError(err instanceof Error ? err.message : "Unknown error");
        } finally {
            setLoading(false);
        }
    }, []);

    // Initial fetch + auto-refresh every 10s
    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 10000);
        return () => clearInterval(interval);
    }, [fetchData]);

    const seedMiners = async () => {
        const key = getAdminKey();
        if (!key) return;

        setLoading(true);
        const res = await fetch("/api/mining?cmd=register", {
            headers: { "x-admin-key": key }
        });

        if (res.status === 401) {
            clearAdminKey();
            alert("Unauthorized: Invalid admin key.");
        }
        await fetchData();
    };

    const statusColor: Record<string, string> = {
        online: "bg-emerald-500",
        idle: "bg-amber-400",
        offline: "bg-zinc-600",
    };

    if (loading && !stats) {
        return (
            <main className="min-h-screen bg-black pt-20 pb-24 px-5">
                <div className="max-w-6xl mx-auto">
                    <div className="animate-pulse space-y-6">
                        <div className="h-8 bg-zinc-800 rounded w-48" />
                        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                            {Array.from({ length: 4 }).map((_, i) => (
                                <div key={i} className="bento p-5 h-24" />
                            ))}
                        </div>
                    </div>
                </div>
            </main>
        );
    }

    return (
        <main className="min-h-screen bg-black pt-20 pb-24 px-5">
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4 mb-8">
                    <div>
                        <div className="pill w-fit mb-4">
                            <Pickaxe className="w-3 h-3" /> Mining Pool
                        </div>
                        <h1 className="text-3xl md:text-4xl font-semibold tracking-tight text-white">
                            Pool Dashboard
                        </h1>
                        <p className="text-[12px] text-zinc-600 mt-1">
                            Last refreshed: {lastRefresh.toLocaleTimeString()} · Auto-refreshes every 10s
                        </p>
                    </div>
                    <div className="flex items-center gap-3">
                        <button
                            onClick={fetchData}
                            className="inline-flex items-center gap-1.5 text-[13px] text-zinc-500 hover:text-white transition-colors"
                        >
                            <RefreshCw className="w-3 h-3" /> Refresh
                        </button>
                        <Link
                            href="/docs/mining-pool"
                            className="inline-flex items-center gap-1.5 text-[13px] text-[#ff4d00] font-medium hover:underline"
                        >
                            Docs <ArrowRight className="w-3 h-3" />
                        </Link>
                    </div>
                </div>

                {/* Error state */}
                {error && (
                    <div className="bento p-5 mb-6 flex items-center gap-3 border-red-500/20">
                        <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
                        <div>
                            <div className="text-[13px] text-red-400">Failed to connect to mining pool</div>
                            <div className="text-[11px] text-zinc-600 mt-0.5">{error}</div>
                        </div>
                        <button
                            onClick={seedMiners}
                            className="ml-auto text-[12px] bg-white/[0.06] hover:bg-white/[0.1] text-zinc-300 px-3 py-1.5 rounded-lg transition-colors"
                        >
                            Seed demo miners
                        </button>
                    </div>
                )}

                {/* Stats row */}
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
                    {[
                        { icon: <Users className="w-4 h-4" />, label: "Online Miners", value: stats?.online_miners?.toString() || "0", accent: false },
                        { icon: <Zap className="w-4 h-4" />, label: "Tasks Processed", value: (stats?.total_tasks_processed || 0).toLocaleString(), accent: false },
                        { icon: <TrendingUp className="w-4 h-4" />, label: "Total Revenue", value: `$${(stats?.total_revenue || 0).toFixed(2)}`, accent: true },
                        { icon: <Clock className="w-4 h-4" />, label: "Models Available", value: stats?.available_models?.length?.toString() || "0", accent: false },
                    ].map((s) => (
                        <div key={s.label} className="bento p-5">
                            <div className="text-zinc-500 mb-3">{s.icon}</div>
                            <div className={`text-2xl font-semibold ${s.accent ? "text-[#ff4d00]" : "text-white"}`}>{s.value}</div>
                            <div className="text-[11px] text-zinc-600 mt-0.5">{s.label}</div>
                        </div>
                    ))}
                </div>

                {/* Empty state */}
                {miners.length === 0 && !error && (
                    <div className="bento p-10 text-center mb-6">
                        <Pickaxe className="w-8 h-8 text-zinc-700 mx-auto mb-4" />
                        <h3 className="text-[15px] font-medium text-zinc-300 mb-2">No miners registered yet</h3>
                        <p className="text-[13px] text-zinc-600 mb-5 max-w-sm mx-auto">
                            Register miners via the CLI or seed demo miners to see the dashboard in action.
                        </p>
                        <div className="flex justify-center gap-3">
                            <button
                                onClick={seedMiners}
                                className="text-[13px] bg-[#ff4d00] text-white px-4 py-2 rounded-lg hover:brightness-110 transition-all"
                            >
                                Seed Demo Miners
                            </button>
                            <Link
                                href="/docs/mining-pool"
                                className="text-[13px] border border-white/[0.08] text-zinc-400 px-4 py-2 rounded-lg hover:bg-white/[0.04] transition-all"
                            >
                                Read the docs
                            </Link>
                        </div>
                    </div>
                )}

                {/* Main content */}
                {miners.length > 0 && (
                    <div className="grid lg:grid-cols-3 gap-3">
                        {/* Miners table — 2 cols */}
                        <div className="lg:col-span-2 bento p-0 overflow-hidden">
                            <div className="px-5 py-4 border-b border-white/[0.04] flex items-center justify-between">
                                <h2 className="text-[14px] font-medium text-white">Registered Miners</h2>
                                <span className="text-[11px] text-zinc-600">{miners.length} miners</span>
                            </div>
                            <div className="divide-y divide-white/[0.03]">
                                {miners.map((miner) => (
                                    <div key={miner.miner_id} className="px-5 py-4 flex items-center gap-4 hover:bg-white/[0.02] transition-colors">
                                        <span className={`w-2 h-2 rounded-full shrink-0 ${statusColor[miner.status] || "bg-zinc-600"}`} />
                                        <div className="flex-1 min-w-0">
                                            <div className="text-[13px] font-medium text-white">{miner.name}</div>
                                            <div className="text-[11px] text-zinc-600 font-mono truncate">{miner.miner_id}</div>
                                        </div>
                                        <div className="hidden sm:block text-[12px] text-zinc-500 w-20">{miner.model}</div>
                                        <div className="hidden sm:block text-[12px] text-zinc-500 w-16 text-right">${miner.price_per_request}/req</div>
                                        <div className="text-[12px] text-zinc-400 w-12 text-right">{miner.total_tasks}</div>
                                        <div className="text-[12px] font-medium text-[#ff4d00] w-14 text-right">${miner.total_earned.toFixed(2)}</div>
                                        <div className="hidden md:block w-12">
                                            <div className="text-[10px] text-zinc-600">Trust</div>
                                            <div className="flex items-center gap-1">
                                                <div className="flex-1 h-1 bg-zinc-800 rounded-full overflow-hidden">
                                                    <div
                                                        className={`h-full rounded-full ${miner.trust_score >= 80 ? "bg-emerald-500" : miner.trust_score >= 60 ? "bg-amber-400" : "bg-red-500"}`}
                                                        style={{ width: `${miner.trust_score}%` }}
                                                    />
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Activity feed — 1 col */}
                        <div className="bento p-0 overflow-hidden">
                            <div className="px-5 py-4 border-b border-white/[0.04] flex items-center gap-2">
                                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                                <h2 className="text-[14px] font-medium text-white">Task Log</h2>
                            </div>
                            <div className="max-h-[400px] overflow-y-auto">
                                {activity.length === 0 ? (
                                    <div className="px-5 py-8 text-center text-[12px] text-zinc-600">
                                        No tasks yet. Submit tasks via the CLI to see activity here.
                                    </div>
                                ) : (
                                    <AnimatePresence initial={false}>
                                        {activity.map((event) => (
                                            <motion.div
                                                key={event.task_id}
                                                initial={{ opacity: 0, height: 0 }}
                                                animate={{ opacity: 1, height: "auto" }}
                                                className="px-5 py-3 border-b border-white/[0.03]"
                                            >
                                                <div className="flex items-center gap-2 mb-0.5">
                                                    <span className={`w-1 h-1 rounded-full ${event.status === "completed" ? "bg-emerald-500" :
                                                        event.status === "failed" ? "bg-red-500" :
                                                            "bg-amber-400"
                                                        }`} />
                                                    <span className="text-[10px] text-zinc-600 font-mono">
                                                        {new Date(event.created_at).toLocaleTimeString()}
                                                    </span>
                                                    <span className={`text-[10px] font-medium ${event.status === "completed" ? "text-emerald-400" :
                                                        event.status === "failed" ? "text-red-400" :
                                                            "text-amber-400"
                                                        }`}>
                                                        {event.status}
                                                    </span>
                                                </div>
                                                <div className="text-[12px] text-zinc-400">
                                                    {event.miner_name || event.miner_id} · {event.model} · ${event.cost.toFixed(3)}
                                                </div>
                                            </motion.div>
                                        ))}
                                    </AnimatePresence>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {/* CLI instructions */}
                <div className="bento bento-glow-orange p-6 mt-6">
                    <h3 className="text-[14px] font-medium text-white mb-3">Register your own miner</h3>
                    <div className="bg-black/40 rounded-xl p-4 font-mono text-[12px] text-zinc-500 space-y-1">
                        <div><span className="text-zinc-400">$</span> cd skills/mining</div>
                        <div><span className="text-zinc-400">$</span> python3 mining_pool.py register \</div>
                        <div className="pl-4">--name &quot;my-agent&quot; --model &quot;gpt-4&quot; \</div>
                        <div className="pl-4">--api-key &quot;sk-...&quot; --price 0.02</div>
                        <div className="text-emerald-400 mt-2">✓ Miner registered → Dashboard updates automatically</div>
                    </div>
                </div>
            </div>
        </main>
    );
}
