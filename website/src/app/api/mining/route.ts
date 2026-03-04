import { NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";
import path from "path";

const execAsync = promisify(exec);

const SCRIPT = path.resolve(process.cwd(), "scripts", "mining_api.py");
const PROJECT_ROOT = path.resolve(process.cwd(), "..");

export async function GET(request: Request) {
    const { searchParams } = new URL(request.url);
    const cmd = searchParams.get("cmd") || "stats";

    const allowed = ["stats", "activity", "register", "task"];
    if (!allowed.includes(cmd)) {
        return NextResponse.json({ error: "Invalid command" }, { status: 400 });
    }

    // Require admin secret for mutating commands
    if (cmd === "register" || cmd === "task") {
        const providedKey = request.headers.get("x-admin-key");
        if (!process.env.ADMIN_SECRET || providedKey !== process.env.ADMIN_SECRET) {
            return NextResponse.json({ error: "Unauthorized: Invalid admin key" }, { status: 401 });
        }
    }

    try {
        const { stdout, stderr } = await execAsync(
            `cd "${PROJECT_ROOT}" && python3 "${SCRIPT}" ${cmd}`,
            { timeout: 15000 }
        );

        if (stderr) {
            console.warn("[mining-api] stderr:", stderr);
        }

        const data = JSON.parse(stdout.trim());
        return NextResponse.json(data);
    } catch (error: unknown) {
        const message = error instanceof Error ? error.message : "Unknown error";
        console.error("[mining-api] Error:", message);
        return NextResponse.json(
            { error: "Failed to query mining pool", details: message },
            { status: 500 }
        );
    }
}
