import { fetchEcosystemStats } from "@/lib/github";

export async function EcosystemStats() {
    const stats = await fetchEcosystemStats();

    const items = [
        { value: stats.totalBounties, label: "TOTAL BOUNTIES", accent: false },
        { value: stats.openBounties, label: "CLAIMABLE", accent: true },
        { value: stats.contributors, label: "CONTRIBUTORS", accent: false },
        { value: stats.totalSkills, label: "SKILLS", accent: false },
        { value: stats.totalTests, label: "TESTS", accent: false },
        { value: stats.completedBounties, label: "COMPLETED", accent: false },
    ];

    return (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-0 border-2 border-white/10 divide-x-2 divide-white/10">
            {items.map((item) => (
                <div key={item.label} className="text-center p-6 hover:bg-white/[0.02] transition-colors">
                    <div className={`text-3xl md:text-4xl font-black tracking-tight ${item.accent ? "text-[#ff3e00]" : "text-white"}`}>
                        {item.value}
                    </div>
                    <div className="text-[10px] tracking-[0.2em] text-zinc-600 uppercase mt-2">
                        {item.label}
                    </div>
                </div>
            ))}
        </div>
    );
}
