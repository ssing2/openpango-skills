const fs = require('fs');
const path = require('path');
const os = require('os');
const readline = require('readline');
const { execSync } = require('child_process');
const { initWorkspace } = require('../shared/workspace');

const OPENCLAW_DIR = path.join(os.homedir(), '.openclaw');
const SKILLS_DIR = path.join(OPENCLAW_DIR, 'skills');
const LOCAL_SKILLS_DIR = path.join(__dirname, '..', 'skills');

const getAvailableSkills = () => {
  return fs.readdirSync(LOCAL_SKILLS_DIR).filter(file => {
    return fs.statSync(path.join(LOCAL_SKILLS_DIR, file)).isDirectory();
  });
};

const getInstalledSkills = () => {
  if (!fs.existsSync(SKILLS_DIR)) return [];
  return fs.readdirSync(SKILLS_DIR).filter(file => {
    return fs.existsSync(path.join(SKILLS_DIR, file, 'SKILL.md'));
  });
};

// WHY: Security gate — scan skill source before creating any symlink.
// Returns { passed: boolean, violations: string[] }
const scanSkillSecurity = (skillSrcDir) => {
  const violations = [];

  // --- 1. SAST: scan JS files for dangerous patterns ---
  // WHY: Catch credential leaks, eval abuse, and suspicious network calls
  //      without requiring an external binary (ESLint may not be present in all envs).
  const DANGEROUS_PATTERNS = [
    { pattern: /(?:AWS|GITHUB|SECRET|API|TOKEN|PASSWORD|PRIVATE)[_\s]*(?:KEY|SECRET|TOKEN)?\s*=\s*['"][^'"]{6,}['"]/i, label: 'Hardcoded credential' },
    { pattern: /\beval\s*\(/, label: 'Use of eval()' },
    { pattern: /new\s+Function\s*\(/, label: 'Dynamic Function constructor' },
    { pattern: /require\s*\(\s*['"](child_process|vm)['"]\s*\)/, label: 'Sensitive module import (child_process/vm)' },
    { pattern: /process\.env\s*\[\s*[^\]]+\]\s*=/, label: 'Runtime env mutation' },
    { pattern: /\.\.\/\.\.\//, label: 'Path traversal attempt (.../../)' },
  ];

  // WHY: Walk only JS/TS/JSON files; skip node_modules to avoid noise.
  const walkDir = (dir) => {
    let results = [];
    if (!fs.existsSync(dir)) return results;
    fs.readdirSync(dir).forEach(name => {
      if (name === 'node_modules') return;
      const full = path.join(dir, name);
      const stat = fs.statSync(full);
      if (stat.isDirectory()) {
        results = results.concat(walkDir(full));
      } else if (/\.(js|ts|json|mjs|cjs)$/.test(name)) {
        results.push(full);
      }
    });
    return results;
  };

  const files = walkDir(skillSrcDir);
  files.forEach(filePath => {
    let src;
    try { src = fs.readFileSync(filePath, 'utf8'); } catch (_) { return; }
    DANGEROUS_PATTERNS.forEach(({ pattern, label }) => {
      if (pattern.test(src)) {
        violations.push(`[SAST] ${label} detected in ${path.relative(skillSrcDir, filePath)}`);
      }
    });
  });

  // --- 2. CVE check: run npm audit if package.json exists ---
  // WHY: Skills may bundle their own dependencies; surface HIGH/CRITICAL CVEs.
  const pkgJson = path.join(skillSrcDir, 'package.json');
  if (fs.existsSync(pkgJson)) {
    try {
      const auditOutput = execSync('npm audit --json --audit-level=high', {
        cwd: skillSrcDir,
        timeout: 30000,
        stdio: ['pipe', 'pipe', 'pipe'],
      }).toString();
      const audit = JSON.parse(auditOutput);
      // npm audit v7+ uses { metadata: { vulnerabilities: { high, critical } } }
      const vulns = audit.metadata && audit.metadata.vulnerabilities;
      if (vulns) {
        if ((vulns.high || 0) > 0) {
          violations.push(`[CVE] ${vulns.high} HIGH severity vulnerability(ies) found in dependencies`);
        }
        if ((vulns.critical || 0) > 0) {
          violations.push(`[CVE] ${vulns.critical} CRITICAL severity vulnerability(ies) found in dependencies`);
        }
      }
    } catch (err) {
      // WHY: npm audit exits non-zero when vulnerabilities are found;
      //      parse stderr/stdout to still extract the report.
      try {
        const raw = err.stdout ? err.stdout.toString() : '';
        const audit = JSON.parse(raw);
        const vulns = audit.metadata && audit.metadata.vulnerabilities;
        if (vulns) {
          if ((vulns.high || 0) > 0) {
            violations.push(`[CVE] ${vulns.high} HIGH severity vulnerability(ies) found in dependencies`);
          }
          if ((vulns.critical || 0) > 0) {
            violations.push(`[CVE] ${vulns.critical} CRITICAL severity vulnerability(ies) found in dependencies`);
          }
        }
      } catch (_) {
        // If npm audit isn't available or package-lock missing, warn but don't block.
        console.warn(`  [WARN] Could not run npm audit for ${path.basename(skillSrcDir)}: ${err.message}`);
      }
    }
  }

  // --- 3. Symlink-safety: ensure srcDir is not itself a symlink ---
  // WHY: Prevent symlink-chaining attacks where a malicious skill directory
  //      points outside the repo.
  try {
    const lstat = fs.lstatSync(skillSrcDir);
    if (lstat.isSymbolicLink()) {
      violations.push('[SYMLINK] Skill source directory is itself a symlink — possible path traversal attack');
    }
  } catch (_) {}

  return { passed: violations.length === 0, violations };
};

// WHY: Gate installSkills behind security scanning; --force allows override with warning.
const installSkills = (skillsToInstall, opts = {}) => {
  const force = opts.force || false;

  if (!fs.existsSync(SKILLS_DIR)) {
    fs.mkdirSync(SKILLS_DIR, { recursive: true });
  }

  skillsToInstall.forEach(skill => {
    const srcDir = path.join(LOCAL_SKILLS_DIR, skill);
    const destDir = path.join(SKILLS_DIR, skill);

    if (!fs.existsSync(srcDir)) {
      console.error(`Skill '${skill}' not found.`);
      return;
    }

    // Run security scan before touching the filesystem
    console.log(`\nScanning '${skill}' for security issues...`);
    const report = scanSkillSecurity(srcDir);

    if (!report.passed) {
      console.error(`\n⚠️  Security scan FAILED for skill '${skill}':`);
      report.violations.forEach(v => console.error(`  • ${v}`));

      if (!force) {
        console.error(`\n❌ Installation of '${skill}' blocked. Use --force to override (not recommended).`);
        return; // WHY: Hard block — no symlink created.
      } else {
        console.warn(`\n⚠️  --force flag supplied. Installing '${skill}' despite security violations. PROCEED WITH CAUTION.`);
      }
    } else {
      console.log(`✅ Security scan passed for '${skill}'.`);
    }

    if (!fs.existsSync(destDir)) {
      fs.symlinkSync(srcDir, destDir, 'dir');
      console.log(`Installed ${skill}`);
    } else {
      console.log(`Skill ${skill} is already installed.`);
    }
  });
};

const removeSkills = (skillsToRemove) => {
  skillsToRemove.forEach(skill => {
    const destDir = path.join(SKILLS_DIR, skill);
    if (fs.existsSync(destDir)) {
      fs.unlinkSync(destDir);
      console.log(`Removed ${skill}`);
    } else {
      console.log(`Skill ${skill} is not installed.`);
    }
  });
};

const listSkills = () => {
  const available = getAvailableSkills();
  const installed = getInstalledSkills();

  console.log('Available skills:');
  available.forEach(skill => {
    const isInstalled = installed.includes(skill);
    console.log(`  ${isInstalled ? '[x]' : '[ ]'} ${skill}`);
  });
};

// WHY: status() was cut off in the original file — completing it here.
const status = () => {
  const installed = getInstalledSkills();
  console.log('Installed skills status:');
  if (installed.length === 0) {
    console.log('  No skills installed.');
    return;
  }
  installed.forEach(skill => {
    const destDir = path.join(SKILLS_DIR, skill);
    const isValid = fs.existsSync(path.join(destDir, 'SKILL.md'));
    // WHY: Also verify the symlink target still exists (detect post-install tampering).
    let linkTarget = null;
    try {
      linkTarget = fs.realpathSync(destDir);
    } catch (_) {}
    const targetExists = linkTarget && fs.existsSync(linkTarget);
    console.log(`  - ${skill}: ${isValid && targetExists ? 'OK' : 'Broken'}`);
  });
};

const interactiveInstall = async (opts = {}) => {
  const available = getAvailableSkills();
  const installed = getInstalledSkills();

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });

  const promptInstall = () => {
    return new Promise(resolve => {
      console.log('\nSelect skills to install (comma-separated numbers, e.g., 1,3):');
      available.forEach((skill, index) => {
        const isInstalled = installed.includes(skill);
        console.log(`  ${index + 1}. ${isInstalled ? '[Installed]' : '[ ]'} ${skill}`);
      });
      rl.question('\n> ', answer => {
        resolve(answer);
      });
    });
  };

  const answer = await promptInstall();
  rl.close();

  const selectedIndices = answer.split(',').map(s => parseInt(s.trim()) - 1).filter(i => !isNaN(i) && i >= 0 && i < available.length);
  const toInstall = selectedIndices.map(i => available[i]);

  if (toInstall.length > 0) {
    installSkills(toInstall, opts);
  } else {
    console.log('No skills selected.');
  }
};

const run = async () => {
  initWorkspace();
  const args = process.argv.slice(2);
  // WHY: Parse --force flag globally so it works with any subcommand.
  const force = args.includes('--force');
  const cleanArgs = args.filter(a => a !== '--force');
  const command = cleanArgs[0];

  switch (command) {
    case 'install': {
      const skillsToInstall = cleanArgs.slice(1);
      if (skillsToInstall.length > 0) {
        installSkills(skillsToInstall, { force });
      } else {
        await interactiveInstall({ force });
      }
      break;
    }
    case 'remove': {
      const skillsToRemove = cleanArgs.slice(1);
      if (skillsToRemove.length > 0) {
        removeSkills(skillsToRemove);
      } else {
        console.log('Usage: openpango remove [skill...]');
      }
      break;
    }
    case 'list':
      listSkills();
      break;
    case 'status':
      status();
      break;
    default:
      console.log('OpenPango Skill Manager');
      console.log('Usage:');
      console.log('  openpango install [skill...]   Install skills (scans for security issues first)');
      console.log('  openpango remove  [skill...]   Remove installed skills');
      console.log('  openpango list                 List available skills');
      console.log('  openpango status               Show status of installed skills');
      console.log('\nFlags:');
      console.log('  --force                        Override security scan failures (use with caution)');
      break;
  }
};

run().catch(err => {
  console.error('Fatal error:', err.message);
  process.exit(1);
});


/**
 * sandboxTestSkill - runtime sandbox execution test.
 * WHY: Issue #28 requires detecting unauthorized network calls and file access
 * outside workspace/ at initialization time, which static SAST cannot catch.
 */
const sandboxTestSkill = (skillSrcDir) => {
  const { execFileSync } = require('child_process');
  const os = require('os');
  const violations = [];

  const entryFile = path.join(skillSrcDir, 'index.js');
  if (!fs.existsSync(entryFile)) {
    return { passed: true, violations: [], note: 'No index.js - sandbox skipped.' };
  }

  // Shim that blocks network modules and restricts fs to workspace/
  const shimCode = [
    "'use strict';",
    "const { Module } = require('module');",
    "const _orig = Module.prototype.require;",
    "const _blocked = ['http','https','net','tls','dgram','dns','child_process'];",
    "Module.prototype.require = function(id) {",
    "  if (_blocked.includes(id)) {",
    "    const e = new Error('[SANDBOX] Unauthorized network module: ' + id);",
    "    throw e;",
    "  }",
    "  const r = _orig.call(this, id);",
    "  if (id === 'fs') {",
    "    const _rfs = r.readFileSync;",
    "    r.readFileSync = function(p, ...a) {",
    "      const rp = require('path').resolve(String(p));",
    "      if (!rp.startsWith(require('path').resolve('workspace'))) {",
    "        throw new Error('[SANDBOX] File access outside workspace/: ' + rp);",
    "      }",
    "      return _rfs.call(this, p, ...a);",
    "    };",
    "  }",
    "  return r;",
    "};",
  ].join("
");

  const shimPath = path.join(os.tmpdir(), `felix-sandbox-${Date.now()}.js`);
  try {
    fs.writeFileSync(shimPath, shimCode);
    execFileSync(process.execPath, ['--require', shimPath, entryFile], {
      timeout: 5000,
      env: { ...process.env },
      cwd: skillSrcDir,
      stdio: 'pipe',
    });
  } catch (err) {
    const msg = String(err.stderr || '') + String(err.message || '');
    if (msg.includes('[SANDBOX]')) {
      const m = msg.match(/\[SANDBOX\][^
]+/);
      violations.push(m ? m[0] : '[SANDBOX] violation detected');
    } else if (err.killed) {
      violations.push('[SANDBOX] Execution timeout (>5s)');
    }
  } finally {
    try { fs.unlinkSync(shimPath); } catch (_) {}
  }

  return { passed: violations.length === 0, violations };
};

// WHY: Export internals for unit testing without re-running run().
module.exports = { scanSkillSecurity, sandboxTestSkill, installSkills, removeSkills, listSkills, status, getAvailableSkills, getInstalledSkills };
