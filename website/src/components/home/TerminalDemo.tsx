"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Terminal as TerminalContainer } from "@/components/ui/Terminal";
import { cn } from "@/lib/utils";

interface TerminalLine {
  text: string;
  type: "command" | "output" | "success" | "error" | "system";
  delay?: number;
}

const DEMO_SEQUENCE: TerminalLine[] = [
  { text: "openpango init workspace", type: "command", delay: 800 },
  { text: "■ initializing file system protocol...", type: "system", delay: 400 },
  { text: "■ fetching digital souls from registry...", type: "system", delay: 600 },
  { text: "✔ soul [planner-01] hydrated. (mem: 1.2GB)", type: "success", delay: 300 },
  { text: "✔ soul [researcher-02] hydrated. (mem: 4.8GB)", type: "success", delay: 300 },
  { text: "✔ soul [coder-03] hydrated. (mem: 2.1GB)", type: "success", delay: 400 },
  { text: "openpango serve --watch", type: "command", delay: 1000 },
  { text: "■ Binding to local sockets...", type: "output", delay: 500 },
  { text: "✔ Workspace active // System nominal on port 3000.", type: "success", delay: 0 },
];

export function TerminalDemo({ isTriggered = false }: { isTriggered?: boolean }) {
  const [lines, setLines] = useState<TerminalLine[]>([]);
  const [currentIndex, setCurrentIndex] = useState(-1);
  const [typedText, setTypedText] = useState("");
  const [isTyping, setIsTyping] = useState(false);

  useEffect(() => {
    if (!isTriggered) return;

    if (currentIndex === -1) {
      const timer = setTimeout(() => setCurrentIndex(0), 400);
      return () => clearTimeout(timer);
    }

    if (currentIndex < DEMO_SEQUENCE.length) {
      const currentLine = DEMO_SEQUENCE[currentIndex];

      if (currentLine.type === "command") {
        setIsTyping(true);
        let charIndex = 0;
        const typeInterval = setInterval(() => {
          if (charIndex <= currentLine.text.length) {
            setTypedText(currentLine.text.substring(0, charIndex));
            charIndex++;
          } else {
            clearInterval(typeInterval);
            setIsTyping(false);
            setLines((prev) => [...prev, currentLine]);
            setTypedText("");
            setTimeout(() => setCurrentIndex((prev) => prev + 1), currentLine.delay || 400);
          }
        }, 50); // Typing speed
        return () => clearInterval(typeInterval);
      } else {
        // Output or success lines appear instantly or after their specific delay
        const timer = setTimeout(() => {
          setLines((prev) => [...prev, currentLine]);
          setCurrentIndex((prev) => prev + 1);
        }, currentLine.delay || 400);
        return () => clearTimeout(timer);
      }
    }
  }, [isTriggered, currentIndex]);

  return (
    <div className="relative group">
      <div className="absolute -inset-1 bg-gradient-to-r from-accent to-purple-600 rounded-xl blur opacity-25 group-hover:opacity-50 transition duration-1000 group-hover:duration-200"></div>
      <TerminalContainer className="min-h-[400px] relative bg-zinc-950/90 border-white/10 shadow-2xl">
        <div className="space-y-3 font-mono text-sm">
          <AnimatePresence>
            {lines.map((line, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2 }}
                className="flex gap-3 leading-relaxed"
              >
                {line.type === "command" && <span className="text-[#ff3e00] font-bold mt-0.5">❯</span>}
                <span className={cn(
                  line.type === "success" ? "text-emerald-400 font-medium shadow-emerald-400/20" :
                  line.type === "system" ? "text-blue-400/80" :
                  line.type === "error" ? "text-rose-400" :
                  line.type === "command" ? "text-zinc-100" :
                  "text-zinc-400"
                )}>
                  {line.text}
                </span>
              </motion.div>
            ))}
          </AnimatePresence>

          {isTyping && (
            <div className="flex gap-3 text-zinc-100 leading-relaxed">
              <span className="text-[#ff3e00] font-bold mt-0.5">❯</span>
              <span>{typedText}</span>
              <motion.div
                animate={{ opacity: [1, 0] }}
                transition={{ repeat: Infinity, duration: 0.8 }}
                className="w-2.5 h-5 bg-[#ff3e00]/80 inline-block align-middle ml-1"
              />
            </div>
          )}

          {!isTyping && currentIndex < DEMO_SEQUENCE.length && isTriggered && (
             <motion.div
                animate={{ opacity: [1, 0] }}
                transition={{ repeat: Infinity, duration: 0.8 }}
                className="w-2.5 h-5 bg-zinc-500/50 inline-block align-middle ml-1 mt-1"
              />
          )}

          {!isTriggered && (
            <div className="flex flex-col items-center justify-center h-full min-h-[300px] space-y-6">
              <div className="w-16 h-16 rounded-full border border-dashed border-zinc-600 flex items-center justify-center animate-[spin_10s_linear_infinite]">
                 <div className="w-8 h-8 rounded-full border-t-2 border-[#ff3e00] animate-[spin_3s_linear_infinite_reverse]"></div>
              </div>
              <div className="text-zinc-500 italic font-mono text-xs uppercase tracking-widest text-center">
                System Standby <br/>
                <span className="text-[#ff3e00]/60 animate-pulse mt-2 inline-block">Awaiting Initialization...</span>
              </div>
            </div>
          )}
        </div>
      </TerminalContainer>
    </div>
  );
}