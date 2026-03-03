#!/usr/bin/env node
/**
 * sandbox-test.js — called by the GitHub Actions workflow to run the dynamic sandbox test
 * on a comma-separated list of skill names passed as argv[2].
 */

const fs = require('fs');
const path = require('path');
const { sandboxTestSkill } = require('../src/cli.js');

const LOCAL_SKILLS_DIR = path.join(__dirname, '..', 'skills');
const REPORT_PATH = path.join(process.cwd(), 'security-report.md');

const skillsArg = process.argv[2] || '';
const skills = skillsArg.split(',').map(s => s.trim()).filter(Boolean);

if (skills.length === 0) {
    process.exit(0);
}

let overallPassed = true;
let report = '';

// Check if report file exists to append to it
if (fs.existsSync(REPORT_PATH)) {
    report = fs.readFileSync(REPORT_PATH, 'utf8');
} else {
    report = '## 🔐 Automated Skill Security Report\n\n';
}

skills.forEach(skill => {
    const srcDir = path.join(LOCAL_SKILLS_DIR, skill);
    if (!fs.existsSync(srcDir)) return;

    console.log(`\nSandbox testing skill: ${skill}`);
    const result = sandboxTestSkill(srcDir);

    if (!result.passed) {
        console.error(`  ❌ SANDBOX FAILED`);
        result.violations.forEach(v => console.error(`    • ${v}`));
        overallPassed = false;

        // Check if we need to add the failing heading
        if (!report.includes(`### \`${skill}\` — ❌ FAILED`)) {
            // If the skill already passed SAST, change the heading to FAILED
            if (report.includes(`### \`${skill}\` — ✅ PASSED`)) {
                report = report.replace(`### \`${skill}\` — ✅ PASSED\nNo security violations detected.\n\n`, `### \`${skill}\` — ❌ FAILED\n| Severity | Violation |\n|---|---|\n`);
            } else {
                report += `### \`${skill}\` — ❌ FAILED\n| Severity | Violation |\n|---|---|\n`;
            }
        }

        // Add violations to the table
        result.violations.forEach(v => {
            report += `| 🔴 CRITICAL | ${v.replace(/^\[\w+\]\s*/, '')} |\n`;
        });
    } else {
        console.log(`  ✅ SANDBOX PASSED`);
    }
});

// Update the overall result line if it exists
if (!overallPassed && report.includes('✅ All scans passed')) {
    report = report.replace('✅ All scans passed', '❌ One or more scans failed');
}

fs.writeFileSync(REPORT_PATH, report, 'utf8');
process.exit(overallPassed ? 0 : 1);
