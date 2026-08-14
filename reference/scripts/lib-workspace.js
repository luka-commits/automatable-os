#!/usr/bin/env node
// Shared workspace reading. Both reference/scripts/inventory.js (the dashboard overview)
// and reference/scripts/workspace-audit.js (the audit) read the same machine, so the
// readers live here once. Two copies would have drifted within a week.
//
// Usage:  const L = require('./lib-workspace.js')(root);   // root = absolute workspace path
//
// ponytail: hand-rolled YAML reader for the `inventory:` block only (list of flat maps,
// inline or block form). Swap for a real parser if config.yaml ever grows nesting there.

const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync } = require('child_process');

const esc = (s) => String(s == null ? '' : s)
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
  .replace(/\s*—\s*/g, ', ');

const norm = (x) => String(x || '').toLowerCase().replace(/[^a-z0-9]/g, '');

const WORK_CLIS = ['gh', 'firecrawl', 'playwright', 'supabase', 'vercel', 'gws', 'claude'];
const BASE_CLIS = ['git', 'node', 'python3', 'uv', 'jq', 'rg', 'docker', 'ffmpeg', 'psql'];
const KNOWN_CLIS = [...WORK_CLIS, ...BASE_CLIS];

// Repos of the projects: read straight out of .git/config, no git call per folder.

function firstSentence(s) {
  if (!s) return '';
  let t = s.split(/(?<=\.)\s+(?=[A-Z(])/)[0].trim();
  if (t.length > 130) t = t.slice(0, 127).replace(/[\s,]+\S*$/, '') + '...';
  return t;
}

const installed = (name) => {
  const bin = name.split(/\s+/)[0].replace(/[^\w.-]/g, '');
  if (!bin) return false;
  const probe = process.platform === 'win32' ? `where ${bin}` : `command -v ${bin}`;
  try { execSync(probe, { stdio: 'ignore' }); return true; } catch { return false; }
};

// Locally registered MCP servers. Connectors wired up in Claude Cowork do NOT show up
// here, they only live in config.yaml, so both sources are merged.
// Measured: `claude mcp list` takes 4.45s, while EVERY file reader in this file adds up
// to 0.15s. It is the only expensive call, because it actually contacts each server. So it
// is the only one cached — everything else stays live, so the dashboard shows your tooling
// as freshly as it shows your tasks. Refetched on a full run (MCP_FRESH=1, set by
// `morning`) or whenever the cache is missing.
function mcpServers() {
  // root is out of scope here (it is a parameter of the factory further down); callers
  // start node with cwd = workspace root, which is enough.
  const cache = path.join(process.cwd(), 'context', '.mcp_cache.json');
  const fresh = process.env.MCP_FRESH === '1';
  if (!fresh) {
    try {
      const d = JSON.parse(fs.readFileSync(cache, 'utf8'));
      if (Array.isArray(d.servers)) return d.servers;
    } catch { /* no cache: then we just ask */ }
  }
  let out;
  try {
    out = execSync('claude mcp list', { stdio: ['ignore', 'pipe', 'ignore'], timeout: 15000 }).toString();
  } catch (e) { out = (e && e.stdout ? e.stdout.toString() : ''); }
  const parsed = parseMcp(out);
  try {
    fs.writeFileSync(cache, JSON.stringify({ at: new Date().toISOString(), servers: parsed }));
  } catch { /* not writable: then it runs every time, only slower */ }
  return parsed;
}

function parseMcp(out) {
  // one line per server:  <name>: <command or url> - ✔ Connected | ! Needs authentication
  return out.split(/\r?\n/).reduce((acc, line) => {
    const colon = line.indexOf(': ');
    const dash = line.lastIndexOf(' - ');
    if (colon < 1 || dash < colon) return acc;
    acc.push({ name: line.slice(0, colon).trim(), status: /✔|✓|Connected/.test(line.slice(dash + 3)) });
    return acc;
  }, []);
}

// Is the key named in key_env present in ~/.config/credentials.env? Only the NAME is
// checked, the value is never read, never printed, never logged.
function hasKey(keyEnv) {
  if (!keyEnv) return false;
  const file = path.join(require('os').homedir(), '.config', 'credentials.env');
  try {
    return new RegExp(`^\\s*(export\\s+)?${keyEnv}\\s*=\\s*\\S`, 'm').test(fs.readFileSync(file, 'utf8'));
  } catch { return false; }
}

// "X ago" for the workspace repo (last commit) — the user's evening backup, at a glance.


// Sign of life for a routine: the newest result file it leaves behind.

function prettyMcp(name) {
  const m = name.match(/^plugin:([^:]+):(.+)$/);
  if (m) return { short: m[2], scope: m[1], fromPlugin: true };
  if (/^claude\.ai\s+/i.test(name)) return { short: name.replace(/^claude\.ai\s+/i, ''), scope: 'claude.ai', fromPlugin: false };
  return { short: name, scope: '', fromPlugin: false };
}

module.exports = function lib(root) {
  root = root || process.cwd();

function readInventory() {
  const file = path.join(root, 'context', 'config.yaml');
  const out = { connectors: [], clis: [], plugins: [], accounts: [], repos: [], routines: [] };
  let text;
  try { text = fs.readFileSync(file, 'utf8'); } catch { return out; }

  const lines = text.split(/\r?\n/);
  let inInv = false, cat = null, entry = null;
  const push = () => { if (cat && entry && out[cat]) out[cat].push(entry); entry = null; };

  for (const raw of lines) {
    const line = raw.replace(/\s+$/, '');
    if (/^inventory:\s*$/.test(line)) { inInv = true; continue; }
    if (!inInv) continue;
    if (/^\S/.test(line)) { push(); break; }              // back to top level -> done
    const bare = line.replace(/^\s+/, '');
    if (!bare || bare.startsWith('#')) continue;

    const catMatch = line.match(/^ {2}(\w+):\s*(\[\])?\s*$/);
    if (catMatch) { push(); cat = catMatch[1]; continue; }
    if (!cat || !out[cat]) continue;

    const item = bare.match(/^-\s*(.*)$/);
    if (item) {
      push();
      entry = {};
      const rest = item[1];
      const inline = rest.match(/^\{(.*)\}\s*$/);
      if (inline) {
        for (const pair of inline[1].split(/,(?=\s*\w+\s*:)/)) {
          const kv = pair.match(/^\s*(\w+)\s*:\s*(.*?)\s*$/);
          if (kv) entry[kv[1]] = val(kv[2]);
        }
      } else {
        const kv = rest.match(/^(\w+)\s*:\s*(.*)$/);
        if (kv) entry[kv[1]] = val(kv[2]);
      }
      continue;
    }
    if (entry) {
      const kv = bare.match(/^(\w+)\s*:\s*(.*)$/);
      if (kv) entry[kv[1]] = val(kv[2]);
    }
  }
  push();
  return out;
}

function val(v) {
  v = v.replace(/\s+#.*$/, '').trim();
  if (v === 'true') return true;
  if (v === 'false') return false;
  return v.replace(/^["']|["']$/g, '');
}

// ---------- live sources ----------

function skillDirs() {
  const home = require('os').homedir();
  const dirs = [];
  const wsSkills = ['.claude/skills', '_claude-template/skills']
    .map((d) => path.join(root, d)).find((d) => fs.existsSync(d));
  if (wsSkills) dirs.push({ dir: wsSkills, scope: 'workspace' });
  const global = path.join(home, '.claude', 'skills');
  if (fs.existsSync(global) && path.resolve(global) !== path.resolve(wsSkills || '')) {
    dirs.push({ dir: global, scope: 'global' });
  }
  // installed plugins bring their own skills along
  try {
    const reg = JSON.parse(fs.readFileSync(path.join(home, '.claude', 'plugins', 'installed_plugins.json'), 'utf8'));
    for (const [key, installs] of Object.entries(reg.plugins || {})) {
      for (const i of installs || []) {
        for (const sub of ['skills', 'plugin/skills']) {
          const d = path.join(i.installPath || '', sub);
          if (fs.existsSync(d)) { dirs.push({ dir: d, scope: 'plugin:' + key.split('@')[0] }); break; }
        }
      }
    }
  } catch {}
  return dirs;
}

function skills() {
  const seen = new Set();
  const list = [];
  for (const { dir, scope } of skillDirs()) {
    let entries = [];
    try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch { continue; }
    for (const e of entries) {
      // symlinked skill folders are the normal case in a grown workspace, so they count too
      if (seen.has(e.name)) continue;
      if (!e.isDirectory() && !(e.isSymbolicLink() && (() => {
        try { return fs.statSync(path.join(dir, e.name)).isDirectory(); } catch { return false; }
      })())) continue;
      const md = path.join(dir, e.name, 'SKILL.md');
      let desc = '';
      try {
        const head = fs.readFileSync(md, 'utf8').split(/\r?\n/).slice(0, 30);
        const i = head.findIndex((l) => /^description:/.test(l));
        if (i >= 0) {
          desc = head[i].replace(/^description:\s*/, '').replace(/^["']|["']\s*$/g, '');
          // block scalar (description: | or >) -> the text is on the following indented lines
          if (/^[|>][-+\d]*$/.test(desc)) {
            desc = head.slice(i + 1).filter((l) => /^\s+\S/.test(l) || !l.trim())
              .map((l) => l.trim()).join(' ').trim();
          }
        }
      } catch { continue; }
      seen.add(e.name);
      list.push({ name: e.name, scope, purpose: firstSentence(desc), full: desc, where: dir });
    }
  }
  return list.sort((a, b) => a.name.localeCompare(b.name));
}

// Installed plugins, read from Claude Code's own registry instead of the config.

// Routines were the last tile read ONLY from config.yaml — so it showed 0 while the
// machine was actually running a dashboard watcher, a morning digest and a crontab entry.
// The same blind spot as with plugins: a hand-maintained list goes stale silently.
// Cloud routines (claude.ai) are invisible to the machine, so those still come from the
// config and are only added to here, never replaced.
function machineRoutines() {
  const out = [];
  const run = (cmd) => {
    try {
      return execSync(cmd, { stdio: ['ignore', 'pipe', 'ignore'], timeout: 5000 }).toString();
    } catch { return ''; }
  };
  if (process.platform === 'darwin' || process.platform === 'linux') {
    for (const line of run('crontab -l').split(/\r?\n/)) {
      const t = line.trim();
      if (!t || t.startsWith('#')) continue;
      const parts = t.split(/\s+/);
      out.push({ name: parts.slice(5).join(' ').slice(0, 60) || t.slice(0, 60),
                 purpose: `crontab, ${parts.slice(0, 5).join(' ')}`, status: true, machine: true });
    }
  }
  if (process.platform === 'darwin') {
    // Maintaining a blocklist against Zoom, Docker and every future updater is hopeless.
    // What matters is not WHO created the job but whether it touches THIS workspace: only
    // agents whose plist points at this folder. Everything else is someone else's software
    // on the same machine and does not belong in your tooling.
    const dir = path.join(require('os').homedir(), 'Library', 'LaunchAgents');
    let files = [];
    try { files = fs.readdirSync(dir).filter((f) => f.endsWith('.plist')); } catch { files = []; }
    for (const f of files) {
      let body = '';
      try { body = fs.readFileSync(path.join(dir, f), 'utf8'); } catch { continue; }
      if (!body.includes(process.cwd())) continue;
      const label = f.replace(/\.plist$/, '');
      const every = body.match(/<key>StartInterval<\/key>\s*<integer>(\d+)/);
      const cal = /StartCalendarInterval/.test(body);
      const watch = /WatchPaths/.test(body);
      const how = watch ? 'launchd, reacts to file changes'
        : cal ? 'launchd, nach Zeitplan'
        : every ? `launchd, alle ${Math.round(Number(every[1]) / 60)} Minuten`
        : 'launchd, laeuft im Hintergrund';
      out.push({ name: label, purpose: how, status: true, machine: true });
    }
  }
  if (process.platform === 'win32') {
    for (const line of run('schtasks /query /fo csv /nh').split(/\r?\n/)) {
      const m = line.match(/^"([^"]+)","([^"]*)","([^"]*)"/);
      if (!m || /\\Microsoft\\/.test(m[1])) continue;
      out.push({ name: m[1].replace(/^\\/, ''), purpose: `Aufgabenplanung, ${m[3]}`, status: /Bereit|Ready/i.test(m[3]), machine: true });
    }
  }
  return out;
}

// Installed and enabled are two different things, and the registry only knows the first:
// installed_plugins.json lists every plugin ever installed, while the on/off state lives in
// settings.json under enabledPlugins (actives only, all set to true). Without that
// distinction the dashboard reports 14 plugins when nine are running — exactly the silent
// error the rest of this file is built against.
function enabledPlugins() {
  const home = require('os').homedir();
  const out = new Set();
  for (const f of ['settings.json', 'settings.local.json']) {
    try {
      const d = JSON.parse(fs.readFileSync(path.join(home, '.claude', f), 'utf8'));
      for (const [k, v] of Object.entries(d.enabledPlugins || {})) if (v) out.add(k);
    } catch { /* file missing or broken: then it simply does not count */ }
  }
  return out;
}

function plugins() {
  const enabled = enabledPlugins();
  try {
    const reg = JSON.parse(fs.readFileSync(
      path.join(require('os').homedir(), '.claude', 'plugins', 'installed_plugins.json'), 'utf8'));
    return Object.entries(reg.plugins || {}).map(([key, installs]) => {
      const [name, market] = key.split('@');
      const i = (installs || [])[0] || {};
      // Return raw data; the caller builds the sentence. This used to call T.pluginFrom(),
      // a lookup table from inventory.js that never existed in this library: the function
      // threw, the catch swallowed it, and the dashboard reported 0 plugins while fourteen
      // were installed. A silent total failure — which is why the catch below returns [].
      return { name, market: market || '?', scope: i.scope || 'user', status: enabled.has(key) };
    }).sort((a, b) => a.name.localeCompare(b.name));
  } catch { return []; }
}

// Two kinds of command line tool, and mixing them is what makes the list feel bloated:
// WORK_CLIS are set up for this workspace and do something specific (firecrawl needs a key,
// gh needs a login). BASE_CLIS are the system floor — present on any developer machine,
// nothing anyone configures. The base ones get ONE summary line, not one row each.

function projectRepos() {
  const found = [];
  const walk = (dir, depth) => {
    let entries = [];
    try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch { return; }
    for (const e of entries) {
      if (!e.isDirectory() || e.name.startsWith('.')) continue;
      const p = path.join(dir, e.name);
      const gitcfg = path.join(p, '.git', 'config');
      if (fs.existsSync(gitcfg)) {
        try {
          const m = fs.readFileSync(gitcfg, 'utf8').match(/url\s*=\s*(\S+)/);
          if (m) found.push({ name: path.relative(root, p), url: m[1] });
        } catch {}
      } else if (depth > 0) walk(p, depth - 1);
    }
  };
  walk(path.join(root, 'projects'), 2);
  return found;
}

function originUrl() {
  // only the workspace's OWN repo counts, not the repo of some parent folder
  try {
    const top = execSync('git rev-parse --show-toplevel', { cwd: root, stdio: ['ignore', 'pipe', 'ignore'] })
      .toString().trim();
    if (path.resolve(top) !== path.resolve(root)) return '';
    return execSync('git remote get-url origin', { cwd: root, stdio: ['ignore', 'pipe', 'ignore'] })
      .toString().trim();
  } catch { return ''; }
}


// ---------- consistency: is the equipment actually wired into CLAUDE.md? ----------
// Two questions, both cheap: does CLAUDE.md point at something that is not installed
// (dead reference), and is something installed that CLAUDE.md never mentions (lies around
// unused)? Skills that are only ever triggered by their own description are not the point,
// the tool routing table is.
function audit() {
  // the global CLAUDE.md counts too — it is loaded in every session, so what stands
  // there is wired up just as much as the workspace file
  const home = require('os').homedir();
  let md = '';
  for (const f of [path.join(root, 'CLAUDE.md'), path.join(root, 'AGENT.md'),
                   path.join(home, '.claude', 'CLAUDE.md')]) {
    try { md += fs.readFileSync(f, 'utf8') + '\n'; } catch {}
  }
  if (!md) return [];
  const mentions = (name) => new RegExp(`\\b${name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'i').test(md);
  const findings = [];

  // dead reference: the routing table names a skill or CLI that is not here
  const have = new Set([...skills().map((x) => x.name), ...KNOWN_CLIS.filter(installed)]);
  const named = new Set();
  for (const m of md.matchAll(/skills?\s+`([\w-]+)`/g)) named.add(m[1]);
  for (const m of md.matchAll(/^\|\s*[^|]+\|\s*`([\w-]+)`/gm)) named.add(m[1]);
  // a plugin skill that is only reachable as plugin:name still counts as present
  const dead = [...named].filter((n) => !have.has(n) && !installed(n));
  if (dead.length) findings.push({ kind: 'dead', items: dead });

  // unused: a configured CLI or key that CLAUDE.md never mentions
  const quietClis = inv.clis.map((c) => c.name).filter((n) => installed(n) && !mentions(n));
  if (quietClis.length) findings.push({ kind: 'cli', items: quietClis });
  const quietKeys = inv.accounts.filter((a) => hasKey(a.key_env) && !mentions(a.name) && !mentions(a.key_env))
    .map((a) => a.name);
  if (quietKeys.length) findings.push({ kind: 'key', items: quietKeys });
  return findings;
}

  // "X ago" for the workspace repo (last commit) — the user's evening backup, at a glance.
  function lastCommit() {
    try {
      return execSync('git log -1 --format=%cr', { cwd: root, stdio: ['ignore', 'pipe', 'ignore'] }).toString().trim();
    } catch { return ''; }
  }

  const fileHere = (rel) => { try { return fs.existsSync(path.join(root, rel)); } catch { return false; } };

  // Working language of the workspace, from config.yaml -> language. Default English.
  const lang = (() => {
    try {
      const m = fs.readFileSync(path.join(root, 'context', 'config.yaml'), 'utf8')
        .match(/^language:\s*["']?(\w+)/m);
      return m && m[1].toLowerCase().startsWith('de') ? 'de' : 'en';
    } catch { return 'en'; }
  })();

  return { root, lang, esc, norm, firstSentence, installed, mcpServers, hasKey, prettyMcp,
    WORK_CLIS, BASE_CLIS, KNOWN_CLIS,
    readInventory, skillDirs, skills, plugins, machineRoutines, projectRepos, originUrl,
    lastCommit, fileHere };
};

module.exports.esc = esc;
module.exports.norm = norm;
module.exports.installed = installed;
module.exports.KNOWN_CLIS = KNOWN_CLIS;
module.exports.WORK_CLIS = WORK_CLIS;
module.exports.BASE_CLIS = BASE_CLIS;
