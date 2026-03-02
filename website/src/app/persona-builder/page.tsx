"use client";

import { useMemo, useState } from "react";
import {
  compilePersonaPayload,
  generateSoulMarkdown,
  personaToYaml,
  toPersonaDocument,
} from "@/lib/persona";

type ExportKind = "json" | "yaml";

const TOOL_PRESETS = [
  "browser",
  "memory",
  "orchestration",
  "figma",
  "web3",
  "comms",
  "security",
  "social-media",
];

function download(filename: string, content: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export default function PersonaBuilderPage() {
  const [coreIdentity, setCoreIdentity] = useState(
    "You are a pragmatic autonomous software agent focused on reliability and clear execution.",
  );
  const [constraints, setConstraints] = useState(
    "- Keep private data private\n- Ask before any irreversible external action\n- Never bypass explicit user safety rules",
  );
  const [tone, setTone] = useState(
    "Direct, technical when needed, and concise by default.",
  );
  const [selectedTools, setSelectedTools] = useState<string[]>([
    "browser",
    "orchestration",
    "memory",
  ]);

  const compiled = useMemo(
    () =>
      compilePersonaPayload({
        coreIdentity,
        constraints,
        tone,
        allowedToolset: selectedTools,
      }),
    [coreIdentity, constraints, tone, selectedTools],
  );

  const soulMarkdown = useMemo(() => generateSoulMarkdown(compiled), [compiled]);
  const personaJson = useMemo(
    () => JSON.stringify(toPersonaDocument(compiled), null, 2),
    [compiled],
  );
  const personaYaml = useMemo(
    () => personaToYaml(toPersonaDocument(compiled)),
    [compiled],
  );

  const toggleTool = (tool: string) => {
    setSelectedTools((prev) =>
      prev.includes(tool) ? prev.filter((t) => t !== tool) : [...prev, tool],
    );
  };

  const exportPersona = (kind: ExportKind) => {
    if (kind === "json") {
      download("persona.json", personaJson, "application/json");
      return;
    }
    download("persona.yaml", personaYaml, "application/yaml");
  };

  return (
    <main className="min-h-screen bg-zinc-950 text-zinc-100 px-6 py-12">
      <div className="max-w-6xl mx-auto space-y-8">
        <header className="space-y-3">
          <p className="text-xs uppercase tracking-[0.2em] text-[#ff3e00]">Persona Builder</p>
          <h1 className="text-4xl font-black tracking-tight">Agent Personality & SOUL Composer</h1>
          <p className="text-zinc-400 max-w-3xl">
            Build a portable agent persona from structured fields. The output is safely normalized,
            transformed to SOUL markdown, and exportable as JSON/YAML.
          </p>
        </header>

        <section className="grid lg:grid-cols-2 gap-6">
          <div className="space-y-5 rounded-xl border border-white/10 bg-zinc-900/50 p-6">
            <div className="space-y-2">
              <label className="text-sm font-semibold">Core Identity</label>
              <textarea
                className="w-full rounded-lg bg-black/40 border border-white/10 px-3 py-2 min-h-24"
                value={coreIdentity}
                onChange={(e) => setCoreIdentity(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-semibold">Constraints</label>
              <textarea
                className="w-full rounded-lg bg-black/40 border border-white/10 px-3 py-2 min-h-28"
                value={constraints}
                onChange={(e) => setConstraints(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-semibold">Tone</label>
              <textarea
                className="w-full rounded-lg bg-black/40 border border-white/10 px-3 py-2 min-h-20"
                value={tone}
                onChange={(e) => setTone(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-semibold">Allowed Toolset</label>
              <div className="flex flex-wrap gap-2">
                {TOOL_PRESETS.map((tool) => {
                  const active = selectedTools.includes(tool);
                  return (
                    <button
                      key={tool}
                      type="button"
                      onClick={() => toggleTool(tool)}
                      className={`px-3 py-1.5 rounded-full text-sm border transition ${
                        active
                          ? "bg-[#ff3e00]/20 border-[#ff3e00] text-white"
                          : "bg-black/40 border-white/10 text-zinc-300"
                      }`}
                    >
                      {tool}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          <div className="space-y-5 rounded-xl border border-white/10 bg-zinc-900/50 p-6">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold">Generated SOUL.md</h2>
              <div className="flex gap-2">
                <button
                  className="px-3 py-1.5 rounded-lg border border-white/10 bg-black/40 text-sm"
                  onClick={() => exportPersona("json")}
                >
                  Export JSON
                </button>
                <button
                  className="px-3 py-1.5 rounded-lg border border-white/10 bg-black/40 text-sm"
                  onClick={() => exportPersona("yaml")}
                >
                  Export YAML
                </button>
              </div>
            </div>

            <pre className="text-xs whitespace-pre-wrap rounded-lg border border-white/10 bg-black/40 p-4 max-h-[460px] overflow-auto">
              {soulMarkdown}
            </pre>
          </div>
        </section>
      </div>
    </main>
  );
}
