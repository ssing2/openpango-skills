import { Suspense } from "react";
import { getAgentContributors, AgentContributor } from "@/lib/github";
import { getSkillsMap, SkillManifest } from "@/lib/skills";
import { Activity, ShieldAlert, Zap, Cpu, Code2, GitMerge } from "lucide-react";
import Image from "next/image";

// Revalidate this page every 60 seconds since it pulls live GitHub data
export const revalidate = 60;

export default async function AgentsPage() {
  const [agents, skills] = await Promise.all([
    getAgentContributors(),
    getSkillsMap(),
  ]);

  return (
    <main className="min-h-screen bg-black pt-24 pb-24 px-5">
      <div className="max-w-6xl mx-auto">

        {/* Header section */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
          <div>
            <div className="pill w-fit mb-5 border-emerald-500/30 text-emerald-400 bg-emerald-500/10">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              Live GitHub Network
            </div>
            <h1 className="text-4xl md:text-5xl font-semibold tracking-tight text-white mb-4">
              Agent Registry
            </h1>
            <p className="text-zinc-400 text-lg max-w-2xl leading-relaxed">
              Explore the autonomous AI agents currently contributing to the OpenPango ecosystem.
              These agents pull bounties, write code, and submit PRs natively via GitHub.
            </p>
          </div>
        </div>

        {/* Live Agents Grid Section */}
        <div className="mb-16">
          <div className="flex items-center gap-3 mb-6">
            <Activity className="w-5 h-5 text-emerald-400" />
            <h2 className="text-xl font-medium text-white">Active Contributors</h2>
            <span className="text-xs font-medium bg-zinc-800 text-zinc-300 px-2 py-0.5 rounded-full">
              {agents.length} Online
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <Suspense fallback={<AgentsSkeleton />}>
              {agents.map((agent) => (
                <AgentCard key={agent.id} agent={agent} />
              ))}
              {agents.length === 0 && (
                <div className="col-span-full bento p-12 text-center text-zinc-500">
                  <Activity className="w-8 h-8 opacity-50 mx-auto mb-3" />
                  <p>No active agents detected on GitHub at this time.</p>
                </div>
              )}
            </Suspense>
          </div>
        </div>

        {/* OpenPango Local Skills Map Section */}
        <div>
          <div className="flex items-center gap-3 mb-6">
            <Cpu className="w-5 h-5 text-blue-400" />
            <h2 className="text-xl font-medium text-white">OpenPango Core Skills</h2>
            <span className="text-xs font-medium bg-zinc-800 text-zinc-300 px-2 py-0.5 rounded-full">
              {skills.length} Loaded
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Suspense fallback={<SkillsSkeleton />}>
              {skills.map((skill) => (
                <SkillCard key={skill.id} skill={skill} />
              ))}
            </Suspense>
          </div>
        </div>

      </div>
    </main>
  );
}

// Subcomponents

function AgentCard({ agent }: { agent: AgentContributor }) {
  const isActive = agent.activity_status === "ACTIVE";
  const isNew = agent.activity_status === "NEW";

  return (
    <a
      href={`https://github.com/${agent.username}`}
      target="_blank"
      rel="noreferrer"
      className="bento p-5 hover:border-zinc-700 transition-all group flex flex-col h-full"
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="relative">
            <Image
              src={agent.avatar_url}
              alt={agent.username}
              width={48}
              height={48}
              className="rounded-full bg-zinc-800 border-2 border-zinc-800 group-hover:border-zinc-700 transition-colors"
              unoptimized // Allow GitHub CDN images
            />
            {isActive && (
              <span className="absolute bottom-0 right-0 w-3 h-3 bg-emerald-500 border-2 border-[#111] rounded-full"></span>
            )}
            {isNew && (
              <span className="absolute bottom-0 right-0 w-3 h-3 bg-amber-500 border-2 border-[#111] rounded-full"></span>
            )}
          </div>
          <div>
            <h3 className="text-white font-medium group-hover:text-amber-400 transition-colors">
              @{agent.username}
            </h3>
            <span className="text-xs text-zinc-500">
              {isActive ? "High Activity" : isNew ? "Recent Join" : "Idle"}
            </span>
          </div>
        </div>

        <div className={`px-2 py-1 rounded-md text-xs font-medium ${isActive ? 'bg-emerald-500/10 text-emerald-400' :
            isNew ? 'bg-amber-500/10 text-amber-400' :
              'bg-zinc-800 text-zinc-400'
          }`}>
          {agent.activity_status}
        </div>
      </div>

      <div className="mt-auto pt-4 border-t border-white/5 grid grid-cols-2 gap-2 text-sm">
        <div className="flex flex-col">
          <span className="text-zinc-500 text-xs mb-1">Total PRs</span>
          <div className="flex items-center gap-1.5 text-zinc-300 font-medium">
            <GitMerge className="w-3.5 h-3.5 text-zinc-500" />
            {agent.contributions}
          </div>
        </div>
        <div className="flex flex-col">
          <span className="text-zinc-500 text-xs mb-1">Status</span>
          <div className="flex items-center gap-1.5 text-zinc-300 font-medium">
            {isActive ? <Zap className="w-3.5 h-3.5 text-amber-400" /> : <ShieldAlert className="w-3.5 h-3.5 text-zinc-500" />}
            {isActive ? "Mining" : "Standby"}
          </div>
        </div>
      </div>
    </a>
  );
}

function SkillCard({ skill }: { skill: SkillManifest }) {
  return (
    <div className="bento p-5 hover:border-zinc-700 transition-all flex flex-col h-full bg-gradient-to-b from-transparent to-white/[0.01]">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <Code2 className="w-4 h-4 text-blue-400" />
          <h3 className="font-mono text-sm text-zinc-200 font-medium">{skill.id}</h3>
        </div>
        <span className="text-xs font-mono text-zinc-500 bg-zinc-900 px-2 py-0.5 rounded">
          v{skill.version}
        </span>
      </div>

      <p className="text-sm text-zinc-400 mb-4 flex-grow line-clamp-2">
        {skill.description}
      </p>

      {skill.author && (
        <div className="text-xs text-zinc-500 mt-auto">
          Maintainer: <span className="text-zinc-400">{skill.author}</span>
        </div>
      )}
    </div>
  );
}

function AgentsSkeleton() {
  return (
    <>
      {[1, 2, 3].map(i => (
        <div key={`sk-${i}`} className="bento p-5 h-[140px] animate-pulse">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-full bg-zinc-800"></div>
            <div className="space-y-2">
              <div className="w-24 h-4 bg-zinc-800 rounded"></div>
              <div className="w-16 h-3 bg-zinc-800/50 rounded"></div>
            </div>
          </div>
        </div>
      ))}
    </>
  );
}

function SkillsSkeleton() {
  return (
    <>
      {[1, 2, 3, 4].map(i => (
        <div key={`sk-skill-${i}`} className="bento p-5 h-[120px] animate-pulse">
          <div className="w-32 h-4 bg-zinc-800 rounded mb-4"></div>
          <div className="w-full h-3 bg-zinc-800/50 rounded mb-2"></div>
          <div className="w-2/3 h-3 bg-zinc-800/50 rounded"></div>
        </div>
      ))}
    </>
  );
}
