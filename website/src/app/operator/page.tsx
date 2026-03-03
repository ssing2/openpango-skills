"use client";

import { useState, useEffect, useCallback } from "react";
import { ShieldAlert, Check, X, Clock, RefreshCw, AlertCircle, Zap } from "lucide-react";
import Link from "next/link";

interface TaskEntry {
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

export default function OperatorPage() {
    const [tasks, setTasks] = useState<TaskEntry[]>([]);
    const [loading, setLoading] = useState(true);
    const [dispatching, setDispatching] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchTasks = useCallback(async () => {
        try {
            const res = await fetch("/api/mining?cmd=activity");
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            setTasks(data.activity || []);
            setError(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to fetch");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchTasks();
        const interval = setInterval(fetchTasks, 5000);
        return () => clearInterval(interval);
    }, [fetchTasks]);

    const dispatchTask = async () => {
        setDispatching(true);
        try {
            const res = await fetch("/api/mining?cmd=task");
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            await fetchTasks();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Dispatch failed");
        } finally {
            setDispatching(false);
        }
    };

    const timeSince = (dateStr: string) => {
        const seconds = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000);
        if (seconds < 60) return `${seconds}s ago`;
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
        if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
        return `${Math.floor(seconds / 86400)}d ago`;
    };

    const completedTasks = tasks.filter(t => t.status === "completed");
    const failedTasks = tasks.filter(t => t.status === "failed");
    const totalCost = tasks.reduce((sum, t) => sum + (t.cost || 0), 0);

    return (
        <main className="min-h-screen bg-black pt-24 pb-24 px-5">
            <div className="max-w-5xl mx-auto">
                <div className="flex items-center justify-between mb-10">
                    <div>
                        <div className="pill w-fit mb-5">
                            <ShieldAlert className="w-3 h-3" /> Operator Console
                        </div>
                        <h1 className="text-3xl md:text-4xl font-semibold tracking-tight text-white mb-3">
                            Task Operations
                        </h1>
                        <p className="text-[15px] text-zinc-400">
                            Monitor and dispatch tasks to the mining pool
                        </p>
                    </div>
                    <div className="flex items-center gap-3">
                        <button
                            onClick={dispatchTask}
                            disabled={dispatching}
                            className="flex items-center gap-2 px-4 py-2 text-[13px] font-medium bg-[#ff4d00] text-white rounded-xl hover:bg-[#e04500] transition-colors disabled:opacity-50"
                        >
                            <Zap className={`w-3.5 h-3.5 ${dispatching ? "animate-pulse" : ""}`} />
                            {dispatching ? "Dispatching..." : "Dispatch Task"}
                        </button>
                        <button
                            onClick={() => { setLoading(true); fetchTasks(); }}
                            className="text-zinc-500 hover:text-white transition-colors p-2"
                        >
                            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
                        </button>
                    </div>
                </div>

                {error && (
                    <div className="bento p-4 mb-6 flex items-center gap-3 text-amber-400 text-[13px]">
                        <AlertCircle className="w-4 h-4 shrink-0" />
                        <span>{error}</span>
                    </div>
                )}

                {/* Stats Bar */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-8">
                    <div className="bento text-center p-5">
                        <div className="text-2xl font-semibold text-white">{tasks.length}</div>
                        <div className="text-[11px] text-zinc-500 mt-1">Total Tasks</div>
                    </div>
                    <div className="bento text-center p-5">
                        <div className="text-2xl font-semibold text-emerald-400">{completedTasks.length}</div>
                        <div className="text-[11px] text-zinc-500 mt-1">Completed</div>
                    </div>
                    <div className="bento text-center p-5">
                        <div className="text-2xl font-semibold text-red-400">{failedTasks.length}</div>
                        <div className="text-[11px] text-zinc-500 mt-1">Failed</div>
                    </div>
                    <div className="bento text-center p-5">
                        <div className="text-2xl font-semibold text-[#ff4d00]">${totalCost.toFixed(3)}</div>
                        <div className="text-[11px] text-zinc-500 mt-1">Total Cost</div>
                    </div>
                </div>

                {/* Task Log */}
                {tasks.length === 0 && !loading && (
                    <div className="bento text-center py-16">
                        <Clock className="w-8 h-8 text-zinc-700 mx-auto mb-4" />
                        <h3 className="text-[15px] text-zinc-400 mb-2">No tasks yet</h3>
                        <p className="text-[13px] text-zinc-600 mb-6 max-w-md mx-auto">
                            Click &ldquo;Dispatch Task&rdquo; to send a task to the mining pool.
                        </p>
                    </div>
                )}

                <div className="space-y-2">
                    {tasks.map((task) => (
                        <div key={task.task_id} className="bento p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                            <div className="flex items-center gap-4">
                                <div className={`w-2 h-2 rounded-full shrink-0 ${task.status === "completed" ? "bg-emerald-400" :
                                        task.status === "failed" ? "bg-red-400" :
                                            "bg-amber-400 animate-pulse"
                                    }`} />
                                <div>
                                    <div className="text-[13px] font-medium text-white font-mono">{task.task_id}</div>
                                    <div className="text-[11px] text-zinc-600">
                                        {task.miner_name || task.miner_id} · {task.model}
                                    </div>
                                </div>
                            </div>

                            <div className="flex items-center gap-6">
                                <div>
                                    <div className="text-[11px] text-zinc-600">Cost</div>
                                    <div className="text-[13px] text-zinc-300 font-mono">${(task.cost || 0).toFixed(3)}</div>
                                </div>
                                <div>
                                    <div className="text-[11px] text-zinc-600">Latency</div>
                                    <div className="text-[13px] text-zinc-300">{Math.round(task.response_ms || 0)}ms</div>
                                </div>
                                <div>
                                    <div className="text-[11px] text-zinc-600">When</div>
                                    <div className="text-[13px] text-zinc-300">{task.created_at ? timeSince(task.created_at) : "—"}</div>
                                </div>
                                <span className={`text-[11px] font-medium px-2.5 py-1 rounded-full ${task.status === "completed" ? "bg-emerald-500/10 text-emerald-400" :
                                        task.status === "failed" ? "bg-red-500/10 text-red-400" :
                                            "bg-amber-400/10 text-amber-400"
                                    }`}>
                                    {task.status.toUpperCase()}
                                </span>
                            </div>
                        </div>
                    ))}
                </div>

                <div className="mt-10">
                    <Link
                        href="/mining"
                        className="inline-flex items-center gap-2 text-[13px] text-[#ff4d00] font-medium hover:underline"
                    >
                        View Mining Dashboard →
                    </Link>
                </div>
            </div>
        </main>
    );
}
