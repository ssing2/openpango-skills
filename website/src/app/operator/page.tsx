"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { ShieldAlert, Check, X, Clock, RefreshCw, AlertCircle, Zap } from "lucide-react";
import Link from "next/link";
import * as Y from "yjs";
import { WebsocketProvider } from "y-websocket";
import { LiveCursors } from "@/components/operator/LiveCursors";

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

const CURSOR_COLORS = ["#ff4d00", "#10b981", "#3b82f6", "#f59e0b", "#ec4899", "#8b5cf6"];

export default function OperatorPage() {
    const [tasks, setTasks] = useState<TaskEntry[]>([]);
    const [loading, setLoading] = useState(true);
    const [dispatching, setDispatching] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Collaboration State
    const [cursors, setCursors] = useState<Map<number, any>>(new Map());
    const ydocRef = useRef<Y.Doc | null>(null);
    const providerRef = useRef<WebsocketProvider | null>(null);
    const tasksArrayRef = useRef<Y.Array<TaskEntry> | null>(null);

    // Init Yjs
    useEffect(() => {
        const ydoc = new Y.Doc();
        ydocRef.current = ydoc;

        // Establish WS connection to local collab server
        const provider = new WebsocketProvider(
            "ws://localhost:1234",
            "openpango-operator-room",
            ydoc
        );
        providerRef.current = provider;

        // Sync tasks array
        const yTasks = ydoc.getArray<TaskEntry>("tasks");
        tasksArrayRef.current = yTasks;

        yTasks.observe(() => {
            // When another client pushes a task to Yjs, merge it locally immediately
            const syncedTasks = yTasks.toArray();
            setTasks((prev) => {
                const map = new Map(prev.map(t => [t.task_id, t]));
                syncedTasks.forEach(t => map.set(t.task_id, t));
                return Array.from(map.values()).sort((a, b) =>
                    new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
                );
            });
        });

        // Sync presence (cursors)
        provider.awareness.setLocalStateField("user", {
            color: CURSOR_COLORS[Math.floor(Math.random() * CURSOR_COLORS.length)]
        });

        provider.awareness.on("change", () => {
            const states = provider.awareness.getStates();
            const newCursors = new Map();
            states.forEach((state: any, clientId: number) => {
                if (clientId !== provider.awareness.clientID && state.cursor) {
                    newCursors.set(clientId, { ...state.cursor, color: state.user?.color || "#ff4d00" });
                }
            });
            setCursors(newCursors);
        });

        return () => {
            provider.disconnect();
            ydoc.destroy();
        };
    }, []);

    // Pointer tracking for live cursors
    useEffect(() => {
        const handlePointerMove = (e: PointerEvent) => {
            if (providerRef.current?.awareness) {
                providerRef.current.awareness.setLocalStateField("cursor", {
                    x: e.clientX,
                    y: e.clientY,
                });
            }
        };
        window.addEventListener("pointermove", handlePointerMove);
        return () => window.removeEventListener("pointermove", handlePointerMove);
    }, []);

    // Fetch initial DB state
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

    // Dispatch and broadcast to Yjs
    const dispatchTask = async () => {
        setDispatching(true);
        try {
            const res = await fetch("/api/mining?cmd=task");
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const result = await res.json();

            // Immediately broadcast the new task to other clients via Yjs
            if (result.task && tasksArrayRef.current) {
                tasksArrayRef.current.push([result.task]);
            }
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
        <main className="min-h-screen bg-black pt-24 pb-24 px-5 relative overflow-hidden">
            <LiveCursors cursors={cursors} />
            <div className="max-w-5xl mx-auto relative z-10">
                <div className="flex flex-col md:flex-row items-start md:items-center justify-between mb-10 gap-4">
                    <div>
                        <div className="flex items-center gap-3 mb-5">
                            <div className="pill w-fit">
                                <ShieldAlert className="w-3 h-3" /> Operator Console
                            </div>
                            {/* Live Collaboration Badge */}
                            {cursors.size > 0 && (
                                <div className="px-3 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-full text-[11px] font-medium flex items-center gap-1.5 animate-in fade-in">
                                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                                    {cursors.size} other{cursors.size === 1 ? "" : "s"} viewing live
                                </div>
                            )}
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
                        <div key={task.task_id} className="bento p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 transition-all duration-300">
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
