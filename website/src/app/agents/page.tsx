"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Activity, Cpu } from "lucide-react";
import { Button } from "@/components/ui/Button";

interface Agent {
  id: string;
  role: string;
  status: "IDLE" | "RUNNING" | "WAITING";
  memory: string;
  compute: "Standard" | "High";
  load: number;
}

const INITIAL_AGENTS: Agent[] = [
  { id: "planner-01", role: "Planner", status: "IDLE", memory: "1.2GB", compute: "Standard", load: 0 },
  { id: "researcher-02", role: "Researcher", status: "RUNNING", memory: "4.8GB", compute: "High", load: 45 },
  { id: "coder-03", role: "Coder", status: "WAITING", memory: "2.1GB", compute: "Standard", load: 12 },
];

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>(INITIAL_AGENTS);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);

  useEffect(() => {
    const interval = setInterval(() => {
      setAgents((prev) => 
        prev.map((agent) => ({
          ...agent,
          load: agent.status === "RUNNING" 
            ? Math.floor(Math.random() * 40) + 40 
            : agent.status === "WAITING"
            ? Math.floor(Math.random() * 10) + 5
            : 0
        }))
      );
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <main className="min-h-screen relative overflow-hidden bg-black pt-40 pb-32 px-6">
      <div className=""></div>
      
      <div className="max-w-6xl mx-auto relative z-10">
        <div className="flex justify-end items-center mb-16">
          <div className="font-mono text-green-400 text-xs tracking-widest border border-green-400/30 bg-green-400/5 px-3 py-1 uppercase flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
            Live Network
          </div>
        </div>

        <motion.div 
          initial={{ opacity: 0, x: -30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6 }}
          className="mb-16"
        >
          <h1 className="text-5xl md:text-7xl font-black uppercase tracking-tighter mb-4">
            Active <span className="text-[#ff3e00]">Souls</span>
          </h1>
          <p className="text-xl text-zinc-400 font-mono tracking-widest">REAL-TIME TELEMETRY</p>
        </motion.div>

        <div className="space-y-4 font-mono text-sm">
          <AnimatePresence mode="popLayout">
            {agents.map((agent) => (
              <motion.div
                key={agent.id}
                layout
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.4 }}
                className="flex flex-col md:flex-row items-start md:items-center justify-between p-6 border border-white/10 bg-zinc-950/50 hover:border-[#ff3e00]/50 transition-colors gap-6"
              >
                <div className="flex items-center gap-6">
                  <div className="p-3 bg-white/5 text-zinc-300">
                    <Activity className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="text-white font-bold text-lg">{agent.role}</div>
                    <div className="text-zinc-500 text-xs">UUID: {agent.id}</div>
                  </div>
                </div>
                
                <div className="flex flex-wrap items-center gap-6 md:gap-12 w-full md:w-auto">
                  <div className="w-24">
                    <div className="text-zinc-600 text-xs mb-1 uppercase tracking-widest">LOAD</div>
                    <div className="flex items-center gap-2">
                      <div className="flex-grow bg-zinc-800 h-1.5 rounded-full overflow-hidden">
                        <motion.div 
                          initial={{ width: 0 }}
                          animate={{ width: `${agent.load}%` }}
                          className={`h-full ${agent.load > 70 ? 'bg-red-500' : 'bg-[#ff3e00]'}`}
                        />
                      </div>
                      <span className="text-xs text-zinc-400 w-8">{agent.load}%</span>
                    </div>
                  </div>
                  <div>
                    <div className="text-zinc-600 text-xs mb-1">COMPUTE</div>
                    <div className="text-zinc-300 flex items-center gap-2">
                      <Cpu className="w-4 h-4 text-zinc-500" /> {agent.compute}
                    </div>
                  </div>
                  <div>
                    <div className="text-zinc-600 text-xs mb-1">MEMORY</div>
                    <div className="text-zinc-300">{agent.memory}</div>
                  </div>
                  <div>
                    <div className="text-zinc-600 text-xs mb-1">STATUS</div>
                    <div className={`px-2 py-1 text-xs border ${
                      agent.status === "RUNNING" ? "border-green-400 text-green-400 bg-green-400/10" :
                      agent.status === "IDLE" ? "border-zinc-500 text-zinc-400 bg-zinc-500/10" :
                      "border-yellow-400 text-yellow-400 bg-yellow-400/10"
                    }`}>
                      {agent.status}
                    </div>
                  </div>
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => setSelectedAgent(agent)}
                  >
                    Inspect
                  </Button>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>

        {/* Inspect Modal */}
        <AnimatePresence>
          {selectedAgent && (
            <div className="fixed inset-0 z-[100] flex items-center justify-center p-6">
              <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={() => setSelectedAgent(null)}
                className="absolute inset-0 bg-black/80 backdrop-blur-md"
              />
              <motion.div 
                initial={{ opacity: 0, scale: 0.9, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.9, y: 20 }}
                className="relative w-full max-w-2xl bg-zinc-900 border border-white/10 rounded-xl overflow-hidden shadow-2xl"
              >
                <div className="bg-zinc-950 px-6 py-4 border-b border-white/10 flex justify-between items-center">
                  <h3 className="font-mono text-sm font-bold uppercase tracking-widest text-[#ff3e00]">
                    Agent Inspection // {selectedAgent.role}
                  </h3>
                  <button 
                    onClick={() => setSelectedAgent(null)}
                    className="text-zinc-500 hover:text-white transition-colors"
                  >
                    [CLOSE]
                  </button>
                </div>
                <div className="p-8 font-mono text-sm space-y-6">
                  <div className="grid grid-cols-2 gap-8">
                    <div>
                      <div className="text-zinc-500 mb-2 uppercase text-xs tracking-tighter">Identity Profile</div>
                      <div className="space-y-1">
                        <div className="text-zinc-300">NAME: <span className="text-white">{selectedAgent.role} Agent</span></div>
                        <div className="text-zinc-300">UUID: <span className="text-white">{selectedAgent.id}</span></div>
                        <div className="text-zinc-300">TYPE: <span className="text-white">Autonomous Sub-Agent</span></div>
                      </div>
                    </div>
                    <div>
                      <div className="text-zinc-500 mb-2 uppercase text-xs tracking-tighter">System Resources</div>
                      <div className="space-y-1">
                        <div className="text-zinc-300">COMPUTE: <span className="text-white">{selectedAgent.compute}</span></div>
                        <div className="text-zinc-300">MEMORY: <span className="text-white">{selectedAgent.memory}</span></div>
                        <div className="text-zinc-300">LOAD: <span className="text-white">{selectedAgent.load}%</span></div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="pt-6 border-t border-white/5">
                    <div className="text-zinc-500 mb-4 uppercase text-xs tracking-tighter">Active Contract (SOUL.md)</div>
                    <div className="bg-black/40 p-4 border border-white/5 rounded text-zinc-400 leading-relaxed italic">
                      &quot;Strict adherence to the workspace protocol is mandatory. No execution outside sandbox boundaries. Communication must remain technical and concise.&quot;
                    </div>
                  </div>

                  <div className="flex justify-end pt-4">
                    <Button variant="primary" onClick={() => setSelectedAgent(null)}>
                      Acknowledge
                    </Button>
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
