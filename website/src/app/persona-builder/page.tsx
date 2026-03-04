"use client";

import { useMemo, useState } from "react";
import {
  compilePersonaPayload,
  generateSoulMarkdown,
  personaToYaml,
  toPersonaDocument,
} from "@/lib/persona";
import { getAdminKey, clearAdminKey } from "@/lib/auth";

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

  const [isDeploying, setIsDeploying] = useState(false);
  const [deployResult, setDeployResult] = useState<{ success?: boolean, message?: string } | null>(null);

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

  const deployPersona = async () => {
    setIsDeploying(true);
    setDeployResult(null);
    try {
      const key = getAdminKey();
      if (!key) {
        setIsDeploying(false);
        return;
      }

      const res = await fetch("/api/deploy-persona", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-admin-key": key
        },
        body: personaJson,
      });
      const data = await res.json();
      if (res.ok && data.success) {
        setDeployResult({ success: true, message: `Deployed dynamically as ID: ${data.minerId}` });
      } else {
        setDeployResult({ success: false, message: data.error || "Deployment failed" });
      }
    } catch (err: any) {
      setDeployResult({ success: false, message: err.message || "Failed to reach server" });
    } finally {
      setIsDeploying(false);
    }
  };

  return (
    <main className="min-h-screen bg-black text-zinc-100 px-5 pt-24 pb-24">
      <div className="max-w-6xl mx-auto space-y-8">
        <header className="space-y-3">
          <p className="pill w-fit mb-5">Persona Builder</p>
          <h1 className="text-3xl md:text-4xl font-semibold tracking-tight text-white">Agent Personality & SOUL Composer</h1>
          <p className="text-zinc-400 max-w-3xl">
            Build a portable agent persona from structured fields. The output is safely normalized,
            transformed to SOUL markdown, and exportable as JSON/YAML. It can also be deployed directly
            into the OpenPango local mining pool.
          </p>
        </header>

        <section className="grid lg:grid-cols-2 gap-6">
          <div className="space-y-5 bento p-6">
            <div className="space-y-2">
              <label className="text-sm font-semibold">Core Identity</label>
              <textarea
                className="w-full rounded-lg bg-black/40 border border-white/10 px-3 py-2 min-h-24 focus:outline-none focus:border-white/30"
                value={coreIdentity}
                onChange={(e) => setCoreIdentity(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-semibold">Constraints</label>
              <textarea
                className="w-full rounded-lg bg-black/40 border border-white/10 px-3 py-2 min-h-28 focus:outline-none focus:border-white/30"
                value={constraints}
                onChange={(e) => setConstraints(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-semibold">Tone</label>
              <textarea
                className="w-full rounded-lg bg-black/40 border border-white/10 px-3 py-2 min-h-20 focus:outline-none focus:border-white/30"
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
                      className={`px-3 py-1.5 rounded-full text-sm border transition flex items-center gap-1.5 ${active
                        ? "bg-[#ff3e00]/20 border-[#ff3e00] text-white"
                        : "bg-black/40 border-white/10 text-zinc-400 hover:text-zinc-200"
                        }`}
                    >
                      {active && <span className="w-1.5 h-1.5 rounded-full bg-[#ff3e00]" />}
                      {tool}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          <div className="space-y-5 bento p-6">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold">Generated SOUL.md</h2>
              <div className="flex gap-2">
                <button
                  className="px-3 py-1.5 rounded-lg border border-white/10 bg-black/40 text-sm hover:bg-white/10 transition-colors"
                  onClick={() => exportPersona("json")}
                >
                  Export JSON
                </button>
                <button
                  className="px-3 py-1.5 rounded-lg border border-white/10 bg-black/40 text-sm hover:bg-white/10 transition-colors"
                  onClick={() => exportPersona("yaml")}
                >
                  Export YAML
                </button>
                <button
                  className="px-4 py-1.5 rounded-lg bg-white text-black font-semibold text-sm hover:bg-zinc-200 transition-colors disabled:opacity-50"
                  onClick={deployPersona}
                  disabled={isDeploying}
                >
                  {isDeploying ? "Deploying..." : "Deploy to Miners"}
                </button>
              </div>
            </div>

            {deployResult && (
              <div className={`p-3 rounded-lg text-sm border ${deployResult.success ? 'bg-green-500/10 border-green-500/20 text-green-400' : 'bg-red-500/10 border-red-500/20 text-red-400'}`}>
                {deployResult.success ? '✅ ' : '❌ '}
                {deployResult.message}
              </div>
            )}

            <pre className="text-xs whitespace-pre-wrap rounded-lg border border-white/10 bg-black/40 p-4 max-h-[460px] overflow-auto font-mono text-zinc-300">
              {soulMarkdown}
            </pre>
          </div>
        </section>
      </div>
    </main>
  );
}
