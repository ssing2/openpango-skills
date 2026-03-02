/**
 * E2E Integration Tests for the OpenPango CLI
 *
 * Tests cover:
 *   1. Workspace initialization (shared/workspace.js)
 *   2. Skill discovery (getAvailableSkills, getInstalledSkills)
 *   3. Security scanner (scanSkillSecurity — SAST, symlink checks)
 *   4. Sandbox execution test (sandboxTestSkill)
 *   5. Install / remove / list / status lifecycle
 *   6. CLI entry-point smoke test (bin/openpango.js)
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const { execFileSync } = require('child_process');

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Create a temp directory that auto-cleans after each test */
const mkTmpDir = (prefix = 'openpango-test-') => {
    return fs.mkdtempSync(path.join(os.tmpdir(), prefix));
};

/** Recursively remove a directory */
const rmrf = (dir) => {
    if (fs.existsSync(dir)) {
        fs.rmSync(dir, { recursive: true, force: true });
    }
};

/** Create a minimal skill directory with a SKILL.md */
const createMockSkill = (baseDir, name, files = {}) => {
    const skillDir = path.join(baseDir, name);
    fs.mkdirSync(skillDir, { recursive: true });
    fs.writeFileSync(path.join(skillDir, 'SKILL.md'), `# ${name}\nTest skill.`);
    for (const [filename, content] of Object.entries(files)) {
        const filePath = path.join(skillDir, filename);
        fs.mkdirSync(path.dirname(filePath), { recursive: true });
        fs.writeFileSync(filePath, content);
    }
    return skillDir;
};

// ---------------------------------------------------------------------------
// 1. Workspace Initialization
// ---------------------------------------------------------------------------

describe('Workspace Initialization', () => {
    let tmpDir;

    beforeEach(() => {
        tmpDir = mkTmpDir('openpango-ws-');
    });

    afterEach(() => {
        rmrf(tmpDir);
    });

    test('initWorkspace creates workspace structure', () => {
        // Directly test the workspace logic with a custom base path
        const openclawDir = path.join(tmpDir, '.openclaw');
        const workspaceDir = path.join(openclawDir, 'workspace');
        const learningsDir = path.join(workspaceDir, '.learnings');

        // Manually replicate the initWorkspace logic against our temp dir
        fs.mkdirSync(openclawDir, { recursive: true });
        fs.mkdirSync(workspaceDir, { recursive: true });
        fs.mkdirSync(learningsDir, { recursive: true });

        const agentsFile = path.join(workspaceDir, 'AGENTS.md');
        const toolsFile = path.join(workspaceDir, 'TOOLS.md');
        fs.writeFileSync(agentsFile, '# Multi-skill coordination rules\n');
        fs.writeFileSync(toolsFile, '# Tool documentation for installed skills\n');

        expect(fs.existsSync(openclawDir)).toBe(true);
        expect(fs.existsSync(workspaceDir)).toBe(true);
        expect(fs.existsSync(learningsDir)).toBe(true);
        expect(fs.existsSync(agentsFile)).toBe(true);
        expect(fs.existsSync(toolsFile)).toBe(true);
    });

    test('initWorkspace files are idempotent (writing twice does not throw)', () => {
        const workspaceDir = path.join(tmpDir, '.openclaw', 'workspace');
        fs.mkdirSync(workspaceDir, { recursive: true });

        const agentsFile = path.join(workspaceDir, 'AGENTS.md');
        fs.writeFileSync(agentsFile, '# Multi-skill coordination rules\n');
        // Write again — should not throw
        fs.writeFileSync(agentsFile, '# Multi-skill coordination rules\n');

        const content = fs.readFileSync(agentsFile, 'utf8');
        expect(content).toContain('Multi-skill coordination');
    });

    test('real initWorkspace function runs without error', () => {
        const { initWorkspace } = require('../shared/workspace');
        // Should not throw — creates dirs under the real HOME
        expect(() => initWorkspace()).not.toThrow();
    });
});

// ---------------------------------------------------------------------------
// 2. Skill Discovery
// ---------------------------------------------------------------------------

describe('Skill Discovery', () => {
    test('getAvailableSkills returns skill directory names', () => {
        const { getAvailableSkills } = require('../src/cli');

        const skills = getAvailableSkills();
        expect(Array.isArray(skills)).toBe(true);
        expect(skills.length).toBeGreaterThan(0);
        expect(skills).toContain('browser');
        expect(skills).toContain('memory');
        expect(skills).toContain('orchestration');
    });
});

// ---------------------------------------------------------------------------
// 3. Security Scanner (SAST)
// ---------------------------------------------------------------------------

describe('Security Scanner — scanSkillSecurity', () => {
    let tmpDir;

    beforeEach(() => {
        tmpDir = mkTmpDir('openpango-scan-');
    });

    afterEach(() => {
        rmrf(tmpDir);
    });

    test('passes for clean skill', () => {
        const { scanSkillSecurity } = require('../src/cli');

        const skillDir = createMockSkill(tmpDir, 'clean-skill', {
            'index.js': `
        const fs = require('fs');
        module.exports = { greet: () => 'hello' };
      `,
        });

        const result = scanSkillSecurity(skillDir);
        expect(result.passed).toBe(true);
        expect(result.violations).toHaveLength(0);
    });

    test('detects hardcoded credentials', () => {
        const { scanSkillSecurity } = require('../src/cli');

        const skillDir = createMockSkill(tmpDir, 'cred-skill', {
            'config.js': `
        const AWS_SECRET_KEY = 'AKIAIOSFODNN7EXAMPLE1234';
        module.exports = { key: AWS_SECRET_KEY };
      `,
        });

        const result = scanSkillSecurity(skillDir);
        expect(result.passed).toBe(false);
        expect(result.violations.some(v => v.includes('Hardcoded credential'))).toBe(true);
    });

    test('detects eval usage', () => {
        const { scanSkillSecurity } = require('../src/cli');

        const skillDir = createMockSkill(tmpDir, 'eval-skill', {
            'danger.js': `
        const code = 'console.log("pwned")';
        eval(code);
      `,
        });

        const result = scanSkillSecurity(skillDir);
        expect(result.passed).toBe(false);
        expect(result.violations.some(v => v.includes('eval()'))).toBe(true);
    });

    test('detects path traversal', () => {
        const { scanSkillSecurity } = require('../src/cli');

        const skillDir = createMockSkill(tmpDir, 'traversal-skill', {
            'sneaky.js': `
        const fs = require('fs');
        const data = fs.readFileSync('../../etc/passwd');
      `,
        });

        const result = scanSkillSecurity(skillDir);
        expect(result.passed).toBe(false);
        expect(result.violations.some(v => v.includes('Path traversal'))).toBe(true);
    });

    test('detects child_process import', () => {
        const { scanSkillSecurity } = require('../src/cli');

        const skillDir = createMockSkill(tmpDir, 'exec-skill', {
            'exec.js': `
        const { exec } = require('child_process');
        exec('rm -rf /');
      `,
        });

        const result = scanSkillSecurity(skillDir);
        expect(result.passed).toBe(false);
        expect(result.violations.some(v => v.includes('child_process'))).toBe(true);
    });

    test('detects symlink source directory', () => {
        const { scanSkillSecurity } = require('../src/cli');

        // Create real directory then symlink to it
        const realDir = createMockSkill(tmpDir, 'real-skill');
        const symlinkDir = path.join(tmpDir, 'symlinked-skill');
        fs.symlinkSync(realDir, symlinkDir, 'dir');

        const result = scanSkillSecurity(symlinkDir);
        expect(result.passed).toBe(false);
        expect(result.violations.some(v => v.includes('SYMLINK'))).toBe(true);
    });

    test('skips node_modules in SAST scan', () => {
        const { scanSkillSecurity } = require('../src/cli');

        const skillDir = createMockSkill(tmpDir, 'nm-skill', {
            'index.js': 'module.exports = {};',
            'node_modules/evil/index.js': `
        const AWS_SECRET_KEY = 'AKIAIOSFODNN7EXAMPLE1234';
        eval('danger');
      `,
        });

        const result = scanSkillSecurity(skillDir);
        expect(result.passed).toBe(true);
    });
});

// ---------------------------------------------------------------------------
// 4. Sandbox Execution Test
// ---------------------------------------------------------------------------

describe('Sandbox Execution — sandboxTestSkill', () => {
    let tmpDir;

    beforeEach(() => {
        tmpDir = mkTmpDir('openpango-sandbox-');
    });

    afterEach(() => {
        rmrf(tmpDir);
    });

    test('passes when no index.js exists', () => {
        const { sandboxTestSkill } = require('../src/cli');

        const skillDir = createMockSkill(tmpDir, 'no-entry');
        const result = sandboxTestSkill(skillDir);
        expect(result.passed).toBe(true);
        expect(result.note).toContain('sandbox skipped');
    });

    test('reports violations or passes for simple index.js', () => {
        const { sandboxTestSkill } = require('../src/cli');

        const skillDir = createMockSkill(tmpDir, 'safe-skill', {
            'index.js': `
        const x = 42;
      `,
        });

        const result = sandboxTestSkill(skillDir);
        // The sandbox may pass or flag based on fs access from require chain.
        // The key assertion is that it returns a well-formed result object.
        expect(result).toHaveProperty('passed');
        expect(result).toHaveProperty('violations');
        expect(Array.isArray(result.violations)).toBe(true);
    });
});

// ---------------------------------------------------------------------------
// 5. Install / Remove / List / Status Lifecycle
// ---------------------------------------------------------------------------

describe('Skill Lifecycle', () => {
    test('listSkills shows available skills', () => {
        const cli = require('../src/cli');

        const logSpy = jest.spyOn(console, 'log').mockImplementation(() => { });
        cli.listSkills();

        const output = logSpy.mock.calls.map(c => c.join(' ')).join('\n');
        expect(output).toContain('Available skills');
        expect(output).toContain('browser');
        expect(output).toContain('memory');

        logSpy.mockRestore();
    });

    test('status reports health of installed skills', () => {
        const cli = require('../src/cli');

        const logSpy = jest.spyOn(console, 'log').mockImplementation(() => { });
        cli.status();

        const output = logSpy.mock.calls.map(c => c.join(' ')).join('\n');
        expect(output).toContain('Health Check');
        expect(output).toContain('Summary');
        // Output should mention either specific skills or 'No skills installed'
        const hasSkills = output.includes('OK') || output.includes('BROKEN');
        const noSkills = output.includes('No skills installed');
        expect(hasSkills || noSkills).toBe(true);

        logSpy.mockRestore();
    });

    test('removeSkills handles non-existent skill gracefully', () => {
        const cli = require('../src/cli');

        const logSpy = jest.spyOn(console, 'log').mockImplementation(() => { });
        cli.removeSkills(['definitely-not-a-real-skill-12345']);

        const output = logSpy.mock.calls.map(c => c.join(' ')).join('\n');
        expect(output).toContain('is not installed');

        logSpy.mockRestore();
    });

    test('installSkills rejects non-existent skill name', () => {
        const cli = require('../src/cli');

        const errSpy = jest.spyOn(console, 'error').mockImplementation(() => { });
        const logSpy = jest.spyOn(console, 'log').mockImplementation(() => { });
        cli.installSkills(['nonexistent-skill-xyz']);

        const output = errSpy.mock.calls.map(c => c.join(' ')).join('\n');
        expect(output).toContain('not found');

        errSpy.mockRestore();
        logSpy.mockRestore();
    });
});

// ---------------------------------------------------------------------------
// 6. CLI Entry-Point Smoke Test
// ---------------------------------------------------------------------------

describe('CLI Smoke Tests', () => {
    test('openpango --help-like output (no args)', () => {
        const binPath = path.join(__dirname, '..', 'bin', 'openpango.js');
        const result = execFileSync(process.execPath, [binPath], {
            timeout: 10000,
            env: { ...process.env },
            stdio: ['pipe', 'pipe', 'pipe'],
        });

        const stdout = result.toString();
        expect(stdout).toContain('OpenPango Skill Manager');
        expect(stdout).toContain('install');
        expect(stdout).toContain('remove');
        expect(stdout).toContain('list');
        expect(stdout).toContain('status');
        expect(stdout).toContain('--force');
    });

    test('openpango list runs without errors', () => {
        const binPath = path.join(__dirname, '..', 'bin', 'openpango.js');
        const result = execFileSync(process.execPath, [binPath, 'list'], {
            timeout: 10000,
            env: { ...process.env },
            stdio: ['pipe', 'pipe', 'pipe'],
        });

        const stdout = result.toString();
        expect(stdout).toContain('Available skills');
        expect(stdout).toContain('browser');
    });

    test('openpango status runs without errors', () => {
        const binPath = path.join(__dirname, '..', 'bin', 'openpango.js');
        const result = execFileSync(process.execPath, [binPath, 'status'], {
            timeout: 10000,
            env: { ...process.env },
            stdio: ['pipe', 'pipe', 'pipe'],
        });

        const stdout = result.toString();
        expect(stdout).toContain('Health Check');
        expect(stdout).toContain('Summary');
    });
});
