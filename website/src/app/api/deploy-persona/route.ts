import { NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";
import path from "path";

const execAsync = promisify(exec);

export async function POST(req: Request) {
    try {
        const body = await req.json();

        // Validate the incoming persona config
        if (!body || !body.coreIdentity) {
            return NextResponse.json({ error: "Invalid persona configuration" }, { status: 400 });
        }

        const providedKey = req.headers.get("x-admin-key");
        if (!process.env.ADMIN_SECRET || providedKey !== process.env.ADMIN_SECRET) {
            return NextResponse.json({ error: "Unauthorized: Invalid admin key" }, { status: 401 });
        }

        // Determine the path to the mining pool script
        // __dirname is inside .next/server/app/api/...
        // process.cwd() is /Users/nico/Desktop/project/website
        // We want to reach skills/mining/mining_pool.py from the project root
        const rootDir = path.join(process.cwd(), "..");
        const miningPoolScript = path.join(rootDir, "skills", "mining", "mining_pool.py");

        // We need to pass the persona config to the python script
        // The easiest way is to pass it as a JSON string argument to a new register command
        // But since the python script doesn't have a CLI for registering yet, we'll
        // execute python code directly to insert the miner

        const minerName = `CustomMiner-${Math.floor(Math.random() * 10000)}`;
        const costPerReq = 0.05; // Default cost for custom miners

        const pythonScript = `
import sys
import json
sys.path.append('${rootDir.replace(/\\/g, '\\\\')}')

try:
    from skills.mining.mining_pool import MiningPool
    pool = MiningPool()
    
    # Register the miner
    miner_id = pool.register_miner(
        name="${minerName}",
        model="custom-persona",
        api_key="persona-builder-key",
        price_per_request=${costPerReq}
    )
    
    # Note: In a full implementation, we would also store the persona fields 
    # (core_identity, constraints, tone, etc) in the database.
    # For now, we just register the miner ID so it shows up in the dashboard.
    
    result = miner_id  # register_miner returns a dict
    print(json.dumps({"success": True, "miner_id": result.get("miner_id", str(result))}))
except Exception as e:
    print(json.dumps({"success": False, "error": str(e)}))
`;

        const { stdout, stderr } = await execAsync(`python3 -c "${pythonScript.replace(/"/g, '\\"')}"`);

        if (stderr && !stdout) {
            console.error("Deploy error:", stderr);
            return NextResponse.json({ error: "Failed to deploy persona to mining pool" }, { status: 500 });
        }

        const result = JSON.parse(stdout.trim());
        if (result.success) {
            return NextResponse.json({ success: true, message: "Deploy successful", minerId: result.miner_id });
        } else {
            return NextResponse.json({ error: result.error || "Deployment failed" }, { status: 500 });
        }

    } catch (error: any) {
        console.error("Deploy API Error:", error);
        return NextResponse.json({ error: error.message || "Internal server error" }, { status: 500 });
    }
}
