import { fetchBounties, type BountyIssue } from "@/lib/github";

const statusConfig = {
    open: {
        label: "CLAIMABLE",
        color: "text-green-400",
        dotColor: "bg-green-400",
    },
    assigned: {
        label: "IN PROGRESS",
        color: "text-[#ffa000]",
        dotColor: "bg-[#ffa000]",
    },
    completed: {
        label: "COMPLETED",
        color: "text-zinc-600",
        dotColor: "bg-zinc-600",
    },
};

function BountyCard({ bounty }: { bounty: BountyIssue }) {
    const config = statusConfig[bounty.status];

    return (
        <a
            href={bounty.url}
            target="_blank"
            rel="noopener noreferrer"
            className="group brutal-card p-6 block"
        >
            <div className="flex items-start justify-between mb-3">
                <div className={`text-[10px] tracking-[0.2em] uppercase ${config.color}`}>
                    #{bounty.number}
                </div>
                {bounty.reward && (
                    <div className="text-xs font-bold text-[#ff3e00] border border-[#ff3e00]/30 px-2 py-0.5">
                        {bounty.reward}
                    </div>
                )}
            </div>

            <h3 className="text-sm font-bold uppercase tracking-tight mb-3 group-hover:text-[#ff3e00] transition-colors line-clamp-2">
                {bounty.title}
            </h3>

            <div className="flex justify-between items-center mt-4">
                <div className={`text-[10px] tracking-[0.2em] uppercase flex items-center gap-2 ${config.color}`}>
                    {bounty.status !== "completed" && (
                        <span className={`w-1.5 h-1.5 ${config.dotColor} ${bounty.status === "open" ? "animate-pulse" : ""}`} />
                    )}
                    {config.label}
                </div>
                {bounty.assignee && (
                    <div className="text-[10px] tracking-[0.1em] text-zinc-600">
                        @{bounty.assignee}
                    </div>
                )}
            </div>
        </a>
    );
}

export async function BountyFeed() {
    const bounties = await fetchBounties();

    const openBounties = bounties.filter((b) => b.status === "open");
    const assignedBounties = bounties.filter((b) => b.status === "assigned");
    const completedBounties = bounties.filter((b) => b.status === "completed");

    const displayed = [
        ...openBounties.slice(0, 6),
        ...assignedBounties.slice(0, 3),
        ...completedBounties.slice(0, 3),
    ].slice(0, 9);

    if (displayed.length === 0) {
        return (
            <div className="text-center text-zinc-600 text-xs tracking-[0.2em] uppercase py-12">
                LOADING BOUNTIES FROM GITHUB...
            </div>
        );
    }

    return (
        <div className="grid md:grid-cols-3 gap-4">
            {displayed.map((bounty) => (
                <BountyCard key={bounty.number} bounty={bounty} />
            ))}
        </div>
    );
}
