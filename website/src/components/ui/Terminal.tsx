import React from "react";
import { cn } from "@/lib/utils";

interface TerminalProps {
  children: React.ReactNode;
  title?: string;
  className?: string;
}

export function Terminal({ children, title = "~/.openpango/workspace", className }: TerminalProps) {
  return (
    <div className={cn("brutal-card rounded-xl bg-black/60 backdrop-blur-3xl overflow-hidden shadow-2xl shadow-[#ff3e00]/10 border border-white/10", className)}>
      <div className="bg-zinc-950/80 px-4 py-3 border-b border-white/10 flex items-center gap-2">
        <div className="flex gap-1.5">
          <div className="w-3 h-3 rounded-full bg-red-500/80"></div>
          <div className="w-3 h-3 rounded-full bg-yellow-500/80"></div>
          <div className="w-3 h-3 rounded-full bg-green-500/80"></div>
        </div>
        <div className="ml-auto font-mono text-xs text-zinc-500">{title}</div>
      </div>
      <div className="p-6 font-mono text-sm leading-relaxed text-zinc-400">
        {children}
      </div>
    </div>
  );
}
