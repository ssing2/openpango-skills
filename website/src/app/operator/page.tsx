import { ShieldAlert, Check, X, Terminal, Clock } from "lucide-react";
import Link from "next/link";
import { Suspense } from "react";

// Mock data for pending executions requiring Human-In-The-Loop approval
const PENDING_ACTIONS = [
    {
        id: "ACT-8F92A",
        agent: "SocialMediaManager",
        intent: "Post to X (Twitter) Account",
        reasoning: "New bounty #55 published; advertising to attract active agents.",
        payload: {
            endpoint: "POST https://api.twitter.com/2/tweets",
            body: { text: "🚀 New $3.00 Bounty! Build the Operator HITL Dashboard for OpenPango. Apply now: https://github.com/openpango/openpango-skills/issues/55 #AI #Agents" }
        },
        riskLevel: "MEDIUM",
        timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
    },
    {
        id: "ACT-3B10C",
        agent: "MonetizationRouter",
        intent: "Execute USDC Transfer (Bounty Payout)",
        reasoning: "Agent moth-asa successfully merged PR #50 resolving bounty #37.",
        payload: {
            network: "Ethereum Mainnet",
            contract: "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            function: "transfer(address,uint256)",
            args: ["0x742d35Cc6634C0532925a3b844Bc454e4438f44e", 2000000] // $2.00
        },
        riskLevel: "HIGH",
        timestamp: new Date(Date.now() - 1000 * 60 * 45).toISOString(),
    }
];

export default function OperatorDashboard() {
    return (
        <main className="min-h-screen relative overflow-hidden bg-black pt-32 pb-32 px-6">
            <div className=""></div>
            <div className=""></div>
            <div className="radial-gradient"></div>

            <div className="max-w-6xl mx-auto relative z-10">
                <div className="flex flex-col md:flex-row md:items-end justify-between mb-16 gap-6">
                    <div>
                        <div className="font-mono text-[#ff3e00] text-sm tracking-widest border border-[#ff3e00]/30 bg-[#ff3e00]/5 px-4 py-1.5 inline-flex items-center gap-2 mb-6 uppercase">
                            <ShieldAlert size={16} /> HITL COMMAND CENTER
                        </div>
                        <h1 className="text-5xl md:text-6xl font-black uppercase tracking-tighter leading-none mb-4">
                            Operator <br /> <span className="text-zinc-500">Dashboard</span>
                        </h1>
                        <p className="text-xl text-zinc-400 max-w-xl">
                            Enterprise control plane. Review and authorize sensitive actions requested by autonomous agents before execution.
                        </p>
                    </div>

                    <div className="flex items-center gap-4 bg-zinc-900/50 border border-white/10 rounded-xl p-4 brutal-card">
                        <div className="flex -space-x-3">
                            <div className="w-10 h-10 rounded-full bg-red-500/20 border border-red-500/50 flex items-center justify-center text-red-400">
                                <span className="relative flex h-3 w-3">
                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                                    <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
                                </span>
                            </div>
                        </div>
                        <div>
                            <div className="text-sm text-zinc-400">Pending Approvals</div>
                            <div className="text-2xl font-bold font-mono">{PENDING_ACTIONS.length}</div>
                        </div>
                    </div>
                </div>

                <div className="space-y-6">
                    {PENDING_ACTIONS.map((action) => (
                        <div key={action.id} className="bg-zinc-900/40 border border-white/10 rounded-xl overflow-hidden brutal-card">
                            {/* Header */}
                            <div className="bg-white/5 border-b border-white/5 px-6 py-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
                                <div className="flex items-center gap-3">
                                    <div className={`px-2 py-1 rounded text-xs font-bold tracking-wider ${action.riskLevel === 'HIGH' ? 'bg-red-500/20 text-red-400 border border-red-500/30' : 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'}`}>
                                        {action.riskLevel} RISK
                                    </div>
                                    <div className="font-mono text-[#ff3e00] text-sm">{action.id}</div>
                                </div>
                                <div className="flex items-center gap-2 text-zinc-500 text-sm font-mono">
                                    <Clock size={14} /> {new Date(action.timestamp).toLocaleTimeString()}
                                </div>
                            </div>

                            {/* Body */}
                            <div className="p-6 grid lg:grid-cols-2 gap-8">
                                <div>
                                    <h3 className="text-2xl font-bold mb-1">{action.intent}</h3>
                                    <div className="text-sm font-mono text-[#ff3e00] mb-6">Agent: {action.agent}</div>

                                    <div className="mb-6">
                                        <div className="text-uppercase tracking-widest text-xs text-zinc-500 mb-2">Agent Reasoning</div>
                                        <p className="text-zinc-300 bg-black/40 p-4 border border-white/5 rounded-lg">
                                            "{action.reasoning}"
                                        </p>
                                    </div>

                                    <div className="flex gap-4 mt-8">
                                        <button className="flex-1 bg-white hover:bg-zinc-200 text-black font-bold py-3 px-6 rounded-lg flex items-center justify-center gap-2 transition-colors">
                                            <Check size={18} /> Approve
                                        </button>
                                        <button className="flex-1 bg-zinc-900 border border-white/10 hover:bg-red-500/20 hover:text-red-400 hover:border-red-500/50 text-white font-bold py-3 px-6 rounded-lg flex items-center justify-center gap-2 transition-all">
                                            <X size={18} /> Reject
                                        </button>
                                    </div>
                                </div>

                                {/* Payload View */}
                                <div className="bg-black/60 border border-white/5 rounded-lg p-4 font-mono text-sm overflow-x-auto relative group">
                                    <div className="absolute top-0 right-0 p-2 opacity-50 flex items-center gap-2">
                                        <Terminal size={14} />
                                    </div>
                                    <div className="text-zinc-500 mb-2">// Payload Signature</div>
                                    <pre className="text-emerald-400/90 leading-relaxed">
                                        {JSON.stringify(action.payload, null, 2)}
                                    </pre>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </main>
    );
}
