import { fetchEcosystemStats } from "@/lib/github";

export async function EcosystemStats() {
    const stats = await fetchEcosystemStats();

    const items = [
        { value: stats.totalBounties, label: "Bounties", accent: false },
        { value: stats.openBounties, label: "Claimable", accent: true },
        { value: stats.contributors, label: "Contributors", accent: false },
        { value: stats.totalSkills, label: "Skills", accent: false },
        { value: stats.totalTests, label: "Tests", accent: false },
        { value: stats.completedBounties, label: "Completed", accent: false },
    ];

    return (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            {items.map((item) => (
                <div key={item.label} className="card text-center p-5">
                    <div className={`text-2xl font-semibold ${item.accent ? "text-[#ff4d00]" : "text-white"}`}>
                        {item.value}
                    </div>
                    <div className="text-[12px] text-zinc-500 mt-1">{item.label}</div>
                </div>
            ))}
        </div>
    );
}
