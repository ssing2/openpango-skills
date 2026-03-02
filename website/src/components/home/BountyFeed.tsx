import { fetchBounties, type BountyIssue } from "@/lib/github";

const statusConfig = {
    open: { label: "Claimable", color: "text-emerald-400", dot: "bg-emerald-400" },
    assigned: { label: "In Progress", color: "text-amber-400", dot: "bg-amber-400" },
    completed: { label: "Completed", color: "text-zinc-600", dot: "bg-zinc-600" },
};

function BountyCard({ bounty }: { bounty: BountyIssue }) {
    const config = statusConfig[bounty.status];
    return (
        <a href={bounty.url} target="_blank" rel="noopener noreferrer" className="card p-5 block group">
            <div className="flex items-center justify-between mb-3">
                <span className={`text-[11px] font-medium ${config.color}`}>#{bounty.number}</span>
                {bounty.reward && (
                    <span className="text-[12px] font-semibold text-[#ff4d00]">{bounty.reward}</span>
                )}
            </div>
            <h3 className="text-[14px] font-medium text-zinc-200 mb-3 leading-snug group-hover:text-white transition-colors line-clamp-2">
                {bounty.title}
            </h3>
            <div className="flex items-center justify-between">
                <div className={`flex items-center gap-1.5 text-[11px] ${config.color}`}>
                    {bounty.status !== "completed" && (
                        <span className={`w-1.5 h-1.5 rounded-full ${config.dot} ${bounty.status === "open" ? "animate-pulse" : ""}`} />
                    )}
                    {config.label}
                </div>
                {bounty.assignee && (
                    <span className="text-[11px] text-zinc-600">@{bounty.assignee}</span>
                )}
            </div>
        </a>
    );
}

export async function BountyFeed() {
    const bounties = await fetchBounties();
    const displayed = [
        ...bounties.filter((b) => b.status === "open").slice(0, 6),
        ...bounties.filter((b) => b.status === "assigned").slice(0, 3),
        ...bounties.filter((b) => b.status === "completed").slice(0, 3),
    ].slice(0, 9);

    if (displayed.length === 0) {
        return <div className="text-center text-zinc-600 text-[13px] py-12">Loading bounties…</div>;
    }

    return (
        <div className="grid md:grid-cols-3 gap-3">
            {displayed.map((b) => <BountyCard key={b.number} bounty={b} />)}
        </div>
    );
}
