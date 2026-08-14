#!/usr/bin/env node
// Workspace-Audit: beurteilt einen Ordner als Arbeitssystem, nicht als Dateihaufen.
//
//   node reference/scripts/workspace-audit.js [--root <pfad>] [--json] [--render] [--selftest]
//
// Misst zehn Dimensionen in drei Gruppen. Die Kriterien prüfen EIGENSCHAFTEN, nie
// Konventionen: nie "gibt es einen context-Ordner", sondern "gibt es genau einen
// erkennbaren Ort für Zustand, und ist der frisch". Nur so läuft es auf fremden Ordnern.
//
// Befund-Disziplin, geerbt aus projects/_external/claude-code-security-review:
// jeder Befund traegt severity UND confidence, unter 0.7 wird gar nicht gemeldet, und
// lieber ein theoretisches Problem übersehen als den Bericht mit Rauschen fluten.
//
// ponytail: alles Mechanische, kein Modell. Das Urteil (Widersprüche, Angemessenheit,
// Empfehlungen) macht der /audit-Skill auf Basis dieser JSON.

const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync } = require('child_process');

const args = process.argv.slice(2);
const argOf = (name) => { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : null; };
const ROOT = path.resolve(argOf('--root') || process.cwd());
const L = require('./lib-workspace.js')(ROOT);
const { esc, norm, skills, plugins, projectRepos, originUrl, installed, mcpServers,
        readInventory, hasKey, KNOWN_CLIS, WORK_CLIS } = L;

// Diese Daten beschreiben die MASCHINE, nicht den geprueften Ordner. Laeuft das Audit
// mit --root auf einen fremden Ordner, gehoeren sie nicht in den Bericht: am 22.07. stand
// im Audit eines Sandkastens "104 Skills, 7 MCP, 46 Jobs" samt einem Job-Namen mit
// Kundenbezug — also der Rechner des Pruefers in einem Bericht ueber jemand anderen.
// Auf dem eigenen Workspace bleibt alles wie gehabt.
const FOREIGN_ROOT = ROOT !== path.resolve(process.cwd());

const DAYS = 90;
const NOW = Date.now();
const days = (ms) => Math.floor((NOW - ms) / 86400000);
const IGNORE = /(^|\/)(\.git|node_modules|\.venv|venv|__pycache__|dist|build|\.next|\.cache|tmp|_tmp)(\/|$)/;
const ARCHIVE = /(^|\/)(_?archiv[e]?|_archive|old|alt|deprecated|skills-(deprecated|archive)|_abgeloest)(\/|$)/i;

// ---------------------------------------------------------------- Dateien einlesen

// Ein verschachteltes Repo ist ein FREMDER Workspace mit eigener Historie und eigener
// Doku. Wer es mitzählt, misst nicht diesen Ordner. Dasselbe gilt für eingekaufte
// Skills und Plugins: die bringen ihre Doku selbst mit.
const NESTED_REPOS = [];
function isNestedRepo(dir) {
  if (path.resolve(dir) === ROOT) return false;
  try { return fs.existsSync(path.join(dir, '.git')); } catch { return false; }
}

function walk(dir, depth = 6, acc = []) {
  let entries = [];
  try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch { return acc; }
  for (const e of entries) {
    const full = path.join(dir, e.name);
    const rel = path.relative(ROOT, full);
    if (IGNORE.test('/' + rel)) continue;
    if (e.isSymbolicLink()) {
      let ok = true;
      try { fs.statSync(full); } catch { ok = false; }
      acc.push({ rel, full, dir: false, symlink: true, broken: !ok, size: 0, mtime: 0 });
      continue;
    }
    if (e.isDirectory()) {
      if (isNestedRepo(full)) { NESTED_REPOS.push(rel); continue; }
      acc.push({ rel, full, dir: true });
      if (depth > 0) walk(full, depth - 1, acc);
    } else {
      let st; try { st = fs.statSync(full); } catch { continue; }
      acc.push({ rel, full, dir: false, size: st.size, mtime: st.mtimeMs, ext: path.extname(e.name) });
    }
  }
  return acc;
}

const FILES = walk(ROOT);
// Dokumente, die über den Skill-Mechanismus gefunden werden, brauchen keinen Link aus
// der CLAUDE.md — sie sind nicht verwaist, sie werden anders entdeckt.
const SELF_DISCOVERED = /(^|\/)\.claude(\/|$)/;
const DOCS = FILES.filter((f) => !f.dir && f.ext === '.md' && !f.symlink);
const OWN_DOCS = DOCS.filter((f) => !SELF_DISCOVERED.test('/' + f.rel));
// Dokumentation gegen Material: was tief im Projektbaum liegt, ist Arbeitsmaterial
// (Eingänge, Arbeitsstaende, Ergebnisse) und muss von nirgends verlinkt sein. Nur was
// oben liegt oder sich README/CLAUDE nennt, ist Wegweiser und gehört erreichbar.
const isDoc = (rel) => {
  const base = path.basename(rel);
  if (/\d{4}-\d{2}-\d{2}/.test(base)) return false;              // datierte Artefakte
  if (/(^|\/)\.|backup|\.bak$/i.test(rel)) return false;          // Backups und Verstecktes
  return rel.split('/').length <= 2
    || /^(README|CLAUDE|AGENTS?|CONTRIBUTING|SETUP|VERSION|ONBOARDING)\.md$/i.test(base);
};
const GUIDE_DOCS = OWN_DOCS.filter((f) => isDoc(f.rel));
const read = (rel) => { try { return fs.readFileSync(path.join(ROOT, rel), 'utf8'); } catch { return ''; } };

// Einstiegspunkte: was eine frische Session ohnehin laedt.
// Nach echtem Ziel entdoppeln: zeigt AGENT.md als Symlink auf CLAUDE.md, ist es EINE
// Datei und darf nicht zweimal als Session-Kosten zaehlen.
const ENTRIES = (() => {
  const seenReal = new Set(); const out = [];
  for (const f of ['CLAUDE.md', 'AGENTS.md', 'AGENT.md', 'README.md']) {
    const full = path.join(ROOT, f);
    if (!fs.existsSync(full)) continue;
    let real = full;
    try { real = fs.realpathSync(full); } catch {}
    if (seenReal.has(real)) continue;
    seenReal.add(real); out.push(f);
  }
  return out;
})();
const GLOBAL_MD = (() => { try { return fs.readFileSync(path.join(os.homedir(), '.claude', 'CLAUDE.md'), 'utf8'); } catch { return ''; } })();
const ENTRY_TEXT = ENTRIES.map(read).join('\n');
const ALL_INSTRUCTIONS = ENTRY_TEXT + '\n' + GLOBAL_MD;

// ---------------------------------------------------------------- Nutzung aus den Session-Logs

// Der einzige Weg, "echte Fähigkeit" von "toter Kontext" zu unterscheiden. Wir zählen
// INVERTIERT (pro bekanntem Namen suchen) — sonst gewinnt Shell-Rauschen wie `do` oder `}`.
function readUsage() {
  const slug = ROOT.replace(/\//g, '-');
  const dir = path.join(os.homedir(), '.claude', 'projects', slug);
  const out = { available: false, sessions: 0, skills: {}, bins: {}, mcp: {}, commands: [], windowDays: DAYS };
  let files = [];
  try { files = fs.readdirSync(dir).filter((f) => f.endsWith('.jsonl')); } catch { return out; }
  const cut = NOW - DAYS * 86400000;
  files = files.filter((f) => { try { return fs.statSync(path.join(dir, f)).mtimeMs > cut; } catch { return false; } });
  if (!files.length) return out;
  out.available = true;
  out.sessions = files.length;

  for (const f of files) {
    let text = '';
    try { text = fs.readFileSync(path.join(dir, f), 'utf8'); } catch { continue; }
    for (const line of text.split('\n')) {
      if (!line.includes('"tool_use"')) continue;
      let o; try { o = JSON.parse(line); } catch { continue; }
      const content = (o.message || {}).content;
      if (!Array.isArray(content)) continue;
      for (const b of content) {
        if (!b || b.type !== 'tool_use') continue;
        const name = b.name || '';
        const inp = b.input || {};
        if (name === 'Skill' && inp.skill) out.skills[inp.skill] = (out.skills[inp.skill] || 0) + 1;
        if (name.startsWith('mcp__')) {
          const srv = name.split('__')[1] || name;
          out.mcp[srv] = (out.mcp[srv] || 0) + 1;
        }
        if (name === 'Bash' && inp.command) out.commands.push(String(inp.command).slice(0, 400));
      }
    }
  }
  // Binaries invertiert zählen: nur bekannte Namen, kein Shell-Rauschen
  const known = new Set([...KNOWN_CLIS, ...readInventory().clis.map((c) => c.name)]);
  for (const cmd of out.commands) {
    const seen = new Set();
    for (const part of cmd.split(/&&|\|\||[|;]/)) {
      const tok = part.trim().split(/\s+/)[0];
      if (known.has(tok) && !seen.has(tok)) { seen.add(tok); out.bins[tok] = (out.bins[tok] || 0) + 1; }
    }
  }
  return out;
}
const USAGE = readUsage();

// ---------------------------------------------------------------- Profil

// Bewusst nachsichtig geparst: `- schlüssel: wert` oder `schlüssel: wert`, Listen mit
// Einrückung. Fehlt die Datei, gilt jeder Slot als "nuetzlich" und der Bericht sagt das.
function readProfile() {
  const raw = read('context/profile.md');
  if (!raw.trim()) return { present: false, tools: [], painpoints: [], team: null, kind: null, channels: [] };
  const p = { present: true, tools: [], painpoints: [], team: null, kind: null, channels: [], local: null };
  let section = null;
  for (const line of raw.split(/\r?\n/)) {
    const key = line.match(/^[-*]?\s*(betrieb|kind|team|kanal|channels|tools|werkzeuge|painpoints|schmerz|lokal|local)\s*:\s*(.*)$/i);
    if (key) {
      section = key[1].toLowerCase();
      const val = key[2].trim();
      if (val) {
        if (/^(team)$/.test(section)) p.team = parseInt(val, 10) || null;
        else if (/^(betrieb|kind)$/.test(section)) p.kind = val;
        else if (/^(lokal|local)$/.test(section)) p.local = /ja|yes|true|lokal/i.test(val);
        else if (/^(kanal|channels)$/.test(section)) p.channels = val.split(/[,;]/).map((x) => x.trim()).filter(Boolean);
        section = null;
      }
      continue;
    }
    const item = line.match(/^\s+[-*]\s+(.*)$/);
    if (item && section) {
      const v = item[1].trim();
      if (/^(tools|werkzeuge)$/.test(section)) {
        const m = v.split(/\s+[—–-]\s+/);
        p.tools.push({ name: m[0].trim(), why: (m[1] || '').trim() });
      } else if (/^(painpoints|schmerz)$/.test(section)) p.painpoints.push(v);
      else if (/^(kanal|channels)$/.test(section)) p.channels.push(v);
    }
  }
  return p;
}
const PROFILE = readProfile();

// ---------------------------------------------------------------- Befunde

const F = [];
// severity: high | medium | low   ·   confidence: 0..1, unter 0.7 wird verworfen
const finding = (dim, severity, confidence, what, why, fix, evidence) =>
  ({ dim, severity, confidence, what, why, fix, evidence: evidence || null });

const dims = [];
function dim(id, group, label, level, metric, findings, note) {
  const kept = (findings || []).filter((f) => f && f.confidence >= 0.7);
  dims.push({ id, group, label, level, metric, note: note || null, findings: kept });
}
const worst = (findings, base) => {
  if (findings.some((f) => f.severity === 'high')) return 'act';
  if (findings.some((f) => f.severity === 'medium')) return 'watch';
  return base || 'ok';
};

// =========================================================== 1. Coverage & routing

(function coverage() {
  const inv = readInventory();
  // Auf einem fremden Ordner zaehlen nur dessen eigene Skills. Die globalen liegen unter
  // ~/.claude/skills und gehoeren dem Pruefer, nicht dem Geprueften — sonst meldet ein
  // Kundenbericht "104 Skills", von denen der Kunde keinen einzigen hat.
  const skillList = FOREIGN_ROOT ? skills().filter((s) => s.scope === 'workspace') : skills();
  const cliNames = new Set(KNOWN_CLIS.filter(installed).map(norm));
  // Dasselbe fuer die MCP-Server: `claude mcp list` beschreibt die Maschine, nicht den Ordner.
  const servers = FOREIGN_ROOT ? [] : mcpServers();
  const mentions = (n) => new RegExp(`\\b${String(n).replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'i').test(ALL_INSTRUCTIONS);
  const findings = [];

  // Vier Quadranten je Fähigkeit: referenziert x benutzt
  const usedSkill = (n) => (USAGE.skills[n] || 0) > 0;
  const usedBin = (n) => (USAGE.bins[n] || 0) > 0;

  const quiet = [];      // referenziert, aber nie benutzt
  const lucky = [];      // benutzt, aber nirgends referenziert
  for (const s of skillList) {
    const ref = mentions(s.name), use = usedSkill(s.name);
    if (use && !ref) lucky.push(s.name);
  }
  for (const c of WORK_CLIS.filter(installed)) {
    const ref = mentions(c), use = usedBin(c);
    if (use && !ref) lucky.push(c);
    if (!use && ref) quiet.push(c);
  }
  for (const a of inv.accounts) {
    if (hasKey(a.key_env) && !mentions(a.name) && !mentions(a.key_env)) quiet.push(a.name);
  }

  if (lucky.length && USAGE.available) {
    findings.push(finding('coverage', 'medium', 0.85,
      `Benutzt, aber nirgends verdrahtet: ${lucky.slice(0, 8).join(', ')}`,
      'Claude only finds this if it happens to come up in conversation. In a fresh session it is gone.',
      'One line in the routing table in CLAUDE.md: which task leads to this tool.',
      { count: lucky.length }));
  }
  if (quiet.length) {
    findings.push(finding('coverage', 'low', 0.75,
      `Set up but unused for ${USAGE.windowDays} days: ${quiet.slice(0, 8).join(', ')}`,
      'Either the occasion never arises, or Claude does not reach for it. Both cost context without carrying anything.',
      'Either tie it to a concrete task, or remove it outright.',
      { count: quiet.length }));
  }

  // Routing: ueberschneidende Trigger fuehren zu stillen Fehlgriffen
  const words = new Map();
  for (const s of skillList) {
    for (const w of (s.full || '').toLowerCase().match(/'[^']{4,30}'/g) || []) {
      const k = w.replace(/'/g, '');
      if (!words.has(k)) words.set(k, []);
      words.get(k).push(s.name);
    }
  }
  const clashes = [...words.entries()].filter(([, v]) => v.length > 1).slice(0, 5);
  if (clashes.length) {
    findings.push(finding('coverage', 'medium', 0.72,
      `${clashes.length} triggers are claimed by more than one skill, e.g. "${clashes[0][0]}" (${clashes[0][1].join(', ')})`,
      'With overlapping triggers, sometimes one starts and sometimes the other. All the user notices is that it is unreliable.',
      'Separate the triggers, or merge the skills.'));
  }

  const noDesc = skillList.filter((s) => !s.purpose).map((s) => s.name);
  if (noDesc.length) {
    findings.push(finding('coverage', 'medium', 0.9,
      `${noDesc.length} Skills ohne Beschreibung: ${noDesc.slice(0, 6).join(', ')}`,
      'Without a description a skill is never found automatically; in practice it does not exist.',
      'Add one description line naming the triggers to each SKILL.md.'));
  }

  const metric = USAGE.available
    ? `${Object.keys(USAGE.skills).length} of ${skillList.length} skills used (${USAGE.windowDays} days)`
    : `${skillList.length} skills, ${servers.length} MCP, usage unknown`;
  dim('coverage', 'Connections', 'Coverage & routing',
    USAGE.available ? worst(findings) : 'unknown', metric, findings);
})();

// =========================================================== 2. Automationsgrad

// Geplante Jobs auf Betriebssystem-Ebene. Der Befund vom 22.07. war genau hier: die
// Config sagte "0 Routinen", waehrend ein launchd-Job taeglich lief und still starb.
// "Nicht eingetragen" und "existiert nicht" sind zwei verschiedene Dinge.
function scheduledJobs() {
  const jobs = [];
  if (FOREIGN_ROOT) return jobs;
  try {
    const out = execSync('launchctl list', { stdio: ['ignore', 'pipe', 'ignore'], maxBuffer: 1e7 }).toString();
    for (const line of out.split('\n')) {
      const m = line.match(/^(-|\d+)\s+(-|\d+)\s+(\S+)$/);
      if (!m || /^com\.apple\./.test(m[3])) continue;
      const exit = m[2] === '-' ? null : parseInt(m[2], 10);
      jobs.push({ label: m[3], exit, running: m[1] !== '-' });
    }
  } catch {}
  try {
    const cron = execSync('crontab -l', { stdio: ['ignore', 'pipe', 'ignore'] }).toString();
    for (const line of cron.split('\n')) {
      if (line.trim() && !line.trim().startsWith('#')) jobs.push({ label: line.trim().slice(0, 60), exit: null, cron: true });
    }
  } catch {}
  return jobs;
}

(function automation() {
  const inv = readInventory();
  const findings = [];

  // Ein Job, der laeuft und scheitert, ist schlimmer als keiner: niemand merkt es.
  const jobs = scheduledJobs();
  const failing = jobs.filter((j) => j.exit !== null && j.exit !== 0);
  if (failing.length) {
    findings.push(finding('automation', 'high', 0.9,
      `${failing.length} scheduled jobs exit with an error: ${failing.slice(0, 4).map((j) => `${j.label} (Exit ${j.exit})`).join(', ')}`,
      'They keep starting on schedule and die immediately. Nobody is told, and whatever they were meant to deliver is simply missing.',
      'Run the job by hand once, read the error, fix the path or the script.',
      { jobs: failing.slice(0, 6) }));
  }
  // Wiederholte Handgriffe sind belegte Automations-Kandidaten
  const sig = new Map();
  for (const cmd of USAGE.commands) {
    const s = cmd.replace(/["'][^"']*["']/g, '_').replace(/\s+/g, ' ').trim().slice(0, 70);
    if (s.length < 12) continue;
    sig.set(s, (sig.get(s) || 0) + 1);
  }
  const repeats = [...sig.entries()].filter(([, n]) => n >= 8).sort((a, b) => b[1] - a[1]).slice(0, 5);
  if (repeats.length) {
    findings.push(finding('automation', 'medium', 0.8,
      `${repeats.length} sequences repeat, the most frequent ${repeats[0][1]} times`,
      'Every repetition costs time and is a chance to get it wrong. Repetition is the best evidence there is for something worth automating.',
      'Turn the most frequent sequence into a command or a routine.',
      { samples: repeats.map(([s, n]) => ({ pattern: s, count: n })) }));
  }
  if (!inv.routines.length && !jobs.length) {
    findings.push(finding('automation', 'low', 0.8,
      'Keine Routine eingerichtet',
      'Everything happens only when someone remembers it. The recurring things are the first to be dropped.',
      'Mit dem anfangen, was taeglich sowieso passiert.'));
  }
  // Auf einem fremden Ordner wurden geplante Jobs bewusst NICHT gelesen (sie beschreiben
  // die Maschine). Das gehoert gesagt statt als "0 Jobs" behauptet — nicht geprueft und
  // nicht vorhanden sind zwei verschiedene Dinge, so steht es oben im Kommentar.
  dim('automation', 'Connections', 'Automation',
    USAGE.available ? worst(findings) : 'unknown',
    `${inv.routines.length} routines, ${FOREIGN_ROOT ? 'scheduled jobs not checked (external folder)' : jobs.length + ' scheduled jobs'}, ${repeats.length} repetition patterns`,
    findings);
})();

// =========================================================== 3. Security

(function security() {
  const findings = [];
  const credFile = path.join(os.homedir(), '.config', 'credentials.env');
  try {
    const st = fs.statSync(credFile);
    const mode = (st.mode & 0o777).toString(8);
    if (mode !== '600') {
      findings.push(finding('security', 'high', 0.9,
        `credentials.env has mode ${mode} instead of 600`,
        'Other accounts on this machine can read the keys.',
        'chmod 600 ~/.config/credentials.env'));
    }
  } catch { /* keine Datei, kein Befund */ }

  // Secrets in getrackten Dateien: nur echte Schlüsselmuster, keine Platzhalter
  let tracked = [];
  try {
    tracked = execSync('git ls-files', { cwd: ROOT, stdio: ['ignore', 'pipe', 'ignore'], maxBuffer: 1e8 })
      .toString().split('\n').filter(Boolean);
  } catch { /* kein Repo */ }
  const SECRET = /(sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}|AKIA[0-9A-Z]{16}|-----BEGIN (RSA |OPENSSH )?PRIVATE KEY-----)/;
  const hits = [];
  for (const rel of tracked.slice(0, 4000)) {
    if (!/\.(md|json|ya?ml|env|js|ts|py|sh|txt|html)$/i.test(rel)) continue;
    const full = path.join(ROOT, rel);
    let st; try { st = fs.statSync(full); } catch { continue; }
    if (st.size > 400000) continue;
    const txt = read(rel);
    const m = txt.match(SECRET);
    // Harte Ausschlussliste (Muster aus claude-code-security-review): Platzhalter in
    // Beispielen sind keine Secrets. Ein Fehlalarm hier kostet mehr Vertrauen, als der
    // Fund wert wäre.
    const PLACEHOLDER = /(your|my|dein|example|sample|placeholder|dummy|test|xxx|abc123|here|token-|\.\.\.|<)/i;
    if (m && !PLACEHOLDER.test(m[0])) hits.push(rel);
    if (hits.length >= 5) break;
  }
  if (hits.length) {
    findings.push(finding('security', 'high', 0.95,
      `Key-like patterns in tracked files: ${hits.join(', ')}`,
      'Anything in the repo leaves this machine with the next push, and stays in the history.',
      'Rotate the key, take it out of the file, move it to ~/.config/credentials.env.',
      { files: hits }));
  }

  // Was darf der Agent ohne Rückfrage? NUR die allow-Liste zaehlt, und was in deny steht,
  // ist geschuetzt, nicht gefaehrlich. Vorher durchsuchte die Regex den ganzen settings-Text
  // inklusive deny-Block — `Bash(rm:*)` in deny (das dich SCHUETZT) loeste den Alarm aus, den
  // es verhindert. Ein Befund ohne Beleg, ausgeloest von der Schutzregel. 23.07.
  // Nur echte destruktive Binaries. Breite Wildcards wie Bash(python3:*) sind hier
  // bewusst NICHT dabei — sie sind fuer den Workspace noetig, und jede zu melden waere
  // das Rauschen, gegen das der ganze Audit gebaut ist.
  const DANGER = /^Bash\((rm|sudo|dd|git push (--force|-f)|curl.*\|\s*(ba)?sh)/;
  let allow = [], deny = [];
  for (const f of ['.claude/settings.json', '.claude/settings.local.json']) {
    try {
      const p = JSON.parse(read(f) || '{}').permissions || {};
      allow = allow.concat(p.allow || []);
      deny = deny.concat(p.deny || []);
    } catch { /* keine oder kaputte Datei */ }
  }
  const denySet = new Set(deny);
  const risky = allow.filter((r) => DANGER.test(r) && !denySet.has(r));
  if (risky.length) {
    findings.push(finding('security', 'medium', 0.8,
      `${risky.length} allow rule${risky.length === 1 ? '' : 's'} let destructive commands through without asking`,
      'A wrong move then runs through without a confirmation, and deny does not apply to this rule.',
      'Narrow the rule, drop it, or put a deny rule against it.',
      { rules: risky }));
  }
  dim('security', 'Connections', 'Security', worst(findings),
    `${tracked.length} tracked files checked`, findings);
})();

// =========================================================== 4. Reachability

(function reach() {
  const findings = [];
  const rels = new Set(FILES.filter((f) => !f.dir).map((f) => f.rel));
  const linksOf = (text) => {
    const out = new Set();
    for (const m of text.matchAll(/\[[^\]]*\]\(([^)\s]+)\)/g)) out.add(m[1]);
    for (const m of text.matchAll(/`([^`\n]+\.[a-z]{2,4})`/gi)) out.add(m[1]);
    return [...out].map((t) => t.split('#')[0].replace(/^\.\//, ''))
      .filter((t) => !/^https?:/.test(t))
      // Platzhalter in Mustern sind keine Verweise: `projects/<gruppe>/`, `skills/*/SKILL.md`
      .filter((t) => !/[<>{}*]|\.\.\./.test(t));
  };
  const byBase = new Map();
  for (const r of rels) {
    const b = path.posix.basename(r);
    byBase.set(b, byBase.has(b) ? byBase.get(b) : r);   // erster Treffer genuegt
  }
  const seen = new Set(ENTRIES);
  const queue = [...ENTRIES];
  const dead = [];
  while (queue.length) {
    const cur = queue.shift();
    const text = read(cur);
    if (!text) continue;
    for (const target of linksOf(text)) {
      if (target.startsWith('~') || target.startsWith('/')) continue;   // außerhalb des Ordners
      const cand = [target, path.posix.join(path.posix.dirname(cur), target)]
        .map((t) => t.replace(/^\.\//, ''));
      let hit = cand.find((c) => rels.has(c));
      // In der Doku steht oft nur der Dateiname (`PROJECTS.md`), nicht der Pfad. Existiert
      // genau eine Datei mit dem Namen, ist das gemeint und kein toter Verweis.
      if (!hit) hit = byBase.get(path.posix.basename(target));
      if (!hit) {
        // Ein Befehl ist kein Verweis. `open context/today.html` und
        // `cmd //c start "" context/today.html` stehen in der Doku als AUSFUEHRBARE Zeile,
        // nicht als Link — wer sie als Pfad liest, meldet drei tote Verweise, die keine
        // sind. Und ein Pruefwerkzeug, das dauerhaft falsch meckert, wird ignoriert:
        // der Fehlalarm ist teurer als der Befund. Gefunden am 23.07. im eigenen Paket.
        const looksLikePath = target.includes('/') && !/\s/.test(target);
        // Ein Journal beschreibt die Vergangenheit, ein Archiv ebenso. Dass dort Genanntes
        // heute nicht mehr existiert, ist der Normalfall und kein Befund.
        const isChronicle = /(JOURNAL|CHANGELOG|HISTORY)/i.test(path.basename(cur)) || ARCHIVE.test('/' + cur);
        if (looksLikePath && !isChronicle && /\.(md|html|ya?ml|json|js|py|sh)$/i.test(target)) {
          dead.push({ from: cur, to: target });
        }
        continue;
      }
      if (!seen.has(hit)) { seen.add(hit); if (hit.endsWith('.md')) queue.push(hit); }
    }
  }
  // Selbstfindende Dokumente: README, weil es im Ordner liegt — und CLAUDE.md/AGENTS.md,
  // weil sie der Einstieg eines Unter-Workspace sind und geladen werden, sobald jemand
  // dort arbeitet. Beide brauchen keinen Link von oben.
  const SELF_ENTRY = /^(README|CLAUDE|AGENTS?)\.md$/i;
  const candidates = GUIDE_DOCS.filter((d) => !ARCHIVE.test('/' + d.rel)
    && !SELF_ENTRY.test(path.basename(d.rel)));
  const orphans = candidates.filter((d) => !seen.has(d.rel));
  const rate = candidates.length ? Math.round((orphans.length / candidates.length) * 100) : 0;
  if (rate > 30 && orphans.length > 3) {
    findings.push(finding('reach', rate > 60 ? 'high' : 'medium', 0.8,
      `${orphans.length} of ${candidates.length} documents (${rate}%) cannot be reached from the entry files`,
      'Nothing points at these documents. Claude never reads them unless someone names the path by hand.',
      'Link them where they belong, or move them to the archive.',
      { examples: orphans.slice(0, 8).map((o) => o.rel) }));
  }
  const deadInEntry = dead.filter((d) => ENTRIES.includes(d.from));
  if (deadInEntry.length) {
    findings.push(finding('reach', 'high', 0.9,
      `${deadInEntry.length} dead links in an entry file`,
      'A link to nothing, in exactly the file every session loads. The pointer looks present but leads nowhere.',
      'Restore the target or remove the link.',
      { examples: deadInEntry.slice(0, 6) }));
  } else if (dead.length > 5) {
    findings.push(finding('reach', 'medium', 0.75,
      `${dead.length} dead links in the documentation`,
      'Every dead link costs a failed attempt, and some trust in the documentation.',
      'Check the targets, update the links.',
      { examples: dead.slice(0, 8) }));
  }
  // Ein toter Symlink ist nicht gleich ein toter Symlink — die Schwere haengt am ORT.
  // In .claude/skills/ ist es ein still totes Kommando (hoch). Anderswo ist es ein
  // kaputter Verweis auf Material, eine fehlende Datei: aergerlich, aber nicht dringend.
  // Vorher wurde alles als high/0.95 mit Skill-Begruendung gemeldet, auch fuenf fehlende
  // Uni-PDFs — genau der Fehlbefund, gegen den dieses Script sonst gebaut ist. 23.07.
  const allBroken = FILES.filter((f) => f.symlink && f.broken && !ARCHIVE.test('/' + f.rel));
  const SKILL_LINK = /(^|\/)\.claude\/skills\//;
  const deadSkills = allBroken.filter((f) => SKILL_LINK.test('/' + f.rel));
  const deadOther = allBroken.filter((f) => !SKILL_LINK.test('/' + f.rel));
  if (deadSkills.length) {
    findings.push(finding('reach', 'high', 0.95,
      `${deadSkills.length} dead skill links`,
      'A dead symlink in .claude/skills/ reports no error, it simply does nothing: the command appears to exist and never happens.',
      'Restore the target or remove the symlink.',
      { examples: deadSkills.slice(0, 6).map((b) => b.rel) }));
  }
  if (deadOther.length) {
    findings.push(finding('reach', 'low', 0.8,
      `${deadOther.length} broken file links`,
      'Symlinks pointing at nothing, usually a source file that was moved or deleted. When it is needed it is not there, though no command breaks because of it.',
      'Check when convenient: bring the file back, or remove the dead link.',
      { examples: deadOther.slice(0, 6).map((b) => b.rel) }));
  }
  // Ohne Dokumente gibt es kein Reachabilitysproblem. Vorher meldete ein Ordner ohne
  // jede Doku "0 von 0 Dokumenten erreichbar" als Handlungsbedarf — ein Alarm ueber eine
  // leere Menge, also genau der Fehlbefund, den dieses Script sonst verbietet.
  dim('reach', 'Knowledge', 'Reachability',
    candidates.length === 0 ? 'unknown' : worst(findings),
    candidates.length === 0
      ? 'no documents present, nothing to reach'
      : `${candidates.length - orphans.length} of ${candidates.length} documents reachable`,
    candidates.length === 0 ? [] : findings);
})();

// =========================================================== 5. Freshness

(function freshness() {
  const findings = [];
  const STATE = /(STATUS|JOURNAL|PROJECTS|ROADMAP|CHANGELOG|NEXT|TODO)/i;
  const STAMP = /(Last updated|Letzte Aktualisierung|Stand)\s*:?\s*\**\s*(\d{4}-\d{2}-\d{2}|\d{2}\.\d{2}\.\d{4})/i;
  const workMtime = Math.max(0, ...FILES.filter((f) => !f.dir && !ARCHIVE.test('/' + f.rel)).map((f) => f.mtime || 0));
  // Ein archiviertes Dokument ist absichtlich alt. Es zu bemängeln heisst, Ablage zu bestrafen.
  const stateDocs = OWN_DOCS.filter((d) => !ARCHIVE.test('/' + d.rel)
    && (STATE.test(path.basename(d.rel)) || STAMP.test(read(d.rel).slice(0, 1500))));
  const stale = [];
  for (const d of stateDocs) {
    const gap = days(d.mtime) - days(workMtime);
    if (gap > 30) stale.push({ file: d.rel, staleDays: days(d.mtime) });
  }
  if (stale.length) {
    findings.push(finding('freshness', stale.length > 2 ? 'high' : 'medium', 0.85,
      `${stale.length} status documents are markedly older than the last work in the folder`,
      'They claim a state that no longer exists. That is worse than having no document, because people believe it.',
      'Bring them up to date, or mark them honestly as historical.',
      { examples: stale.slice(0, 6) }));
  }
  dim('freshness', 'Knowledge', 'Freshness', worst(findings),
    `${stateDocs.length} status documents, ${stale.length} stale`, findings);
})();

// =========================================================== 6. Dead weight

(function bloat() {
  const findings = [];
  const bytes = ENTRIES.reduce((n, f) => n + read(f).length, 0) + GLOBAL_MD.length;
  const tokens = Math.round(bytes / 4);
  if (tokens > 12000) {
    findings.push(finding('bloat', tokens > 25000 ? 'high' : 'medium', 0.8,
      `The entry files cost roughly ${tokens.toLocaleString('en-US')} tokens per session`,
      'Das faellt bei jeder einzelnen Unterhaltung an, bevor irgendetwas passiert.',
      'Move rarely used rules into a reference file and have them read only when needed.',
      { tokens }));
  }
  // Mehrere Einstiegsdateien sind LEGITIM: verschiedene Agenten lesen verschiedene Namen
  // (Claude Code liest CLAUDE.md, andere lesen AGENTS.md oder AGENT.md). Ihre Doppelung
  // ist deshalb kein Dead weight-Befund. Das echte Risiko ist, dass sie auseinanderlaufen —
  // dann arbeitet ein Agent still mit einer aelteren Fassung.
  const entryTexts = ENTRIES.map((f) => ({ f, t: read(f).replace(/\s+/g, ' ').trim() }));
  for (let i = 0; i < entryTexts.length; i++) {
    for (let j = i + 1; j < entryTexts.length; j++) {
      const a = entryTexts[i], b = entryTexts[j];
      if (!a.t.length || !b.t.length) continue;
      // "Zwillinge" heisst: ueber 80 % gemeinsame Absaetze. Dann sind sie als Kopie gemeint.
      const pa = new Set(read(a.f).split(/\n\s*\n/).map((x) => x.replace(/\s+/g, ' ').trim()).filter((x) => x.length > 80));
      const pb = new Set(read(b.f).split(/\n\s*\n/).map((x) => x.replace(/\s+/g, ' ').trim()).filter((x) => x.length > 80));
      if (!pa.size || !pb.size) continue;
      const shared = [...pa].filter((x) => pb.has(x)).length;
      const ratio = shared / Math.max(pa.size, pb.size);
      if (ratio < 0.8) continue;
      if (a.t === b.t) continue;                       // identisch, alles gut
      const onlyA = [...pa].filter((x) => !pb.has(x)).length;
      const onlyB = [...pb].filter((x) => !pa.has(x)).length;
      findings.push(finding('bloat', 'high', 0.9,
        `${a.f} and ${b.f} are twins that have drifted apart (${onlyA} and ${onlyB} paragraphs exist in only one)`,
        'Two entry files for different agents are fine. Two versions of the same rules are not: from now on one agent works from an older state, and nobody is told.',
        'Make one of them the truth and point the other at it as a symlink, so the drift cannot come back.',
        { dateien: [a.f, b.f], nurInA: onlyA, nurInB: onlyB }));
    }
  }

  // Duplikate: derselbe Absatz an mehreren Orten
  const TWINS = new Set(ENTRIES);
  const blocks = new Map();
  for (const f of [...ENTRIES, ...OWN_DOCS.slice(0, 200).map((d) => d.rel)]) {
    const text = read(f);
    for (const para of text.split(/\n\s*\n/)) {
      const key = para.replace(/\s+/g, ' ').trim();
      if (key.length < 200) continue;
      if (!blocks.has(key)) blocks.set(key, new Set());
      blocks.get(key).add(f);
    }
  }
  // Absaetze, die nur zwischen den Einstiegsdateien doppelt sind, sind oben schon behandelt.
  // Und Backups zaehlen nie: eine Backupskopie SOLL identisch sein.
  const dupes = [...blocks.entries()].filter(([, files]) => {
    const real = [...files].filter((f) => !/backup|\.bak$/i.test(f));
    return new Set(real.filter((f) => !TWINS.has(f))).size >= 1 && real.length > 1;
  });
  if (dupes.length) {
    findings.push(finding('bloat', dupes.length > 5 ? 'medium' : 'low', 0.8,
      `${dupes.length} blocks of text appear word for word in several files`,
      'The same fact in two places means one of them eventually goes wrong, and nobody notices which.',
      'Make one place the truth and have the others point at it.',
      { examples: dupes.slice(0, 4).map(([k, v]) => ({ files: [...v], preview: k.slice(0, 90) })) }));
  }
  dim('bloat', 'Knowledge', 'Dead weight', worst(findings), `~${tokens.toLocaleString('en-US')} tokens per session`, findings);
})();

// =========================================================== 7. Cold start

(function coldstart() {
  const findings = [];
  if (!ENTRIES.length) {
    findings.push(finding('coldstart', 'high', 0.95,
      'No entry file (CLAUDE.md, AGENTS.md or README.md)',
      'A fresh session knows nothing about this folder and starts from zero every time.',
      'Create a CLAUDE.md: what this is, where things live, how the work is done.'));
  } else {
    const t = ENTRY_TEXT.toLowerCase();
    const missing = [];
    if (!/(ordner|struktur|folder|structure|verzeichnis)/.test(t)) missing.push('the folder structure');
    if (!/(skill|kommando|command|\/[a-z-]{3,})/.test(t)) missing.push('the available commands');
    if (!/(zweck|purpose|wofuer|ziel|was ist)/.test(t)) missing.push('den Zweck des Ordners');
    if (missing.length) {
      findings.push(finding('coldstart', missing.length > 1 ? 'medium' : 'low', 0.75,
        `The entry file does not explain: ${missing.join(', ')}`,
        'A new person, or a fresh session, has to piece this together instead of getting started.',
        'Two or three lines on each, at the top of the entry file.'));
    }
  }
  dim('coldstart', 'Knowledge', 'Cold start', worst(findings),
    ENTRIES.length ? `${ENTRIES.join(', ')}` : 'no entry file', findings);
})();

// =========================================================== 8. Decision memory

(function decisions() {
  const findings = [];
  const WHY = /(entschieden|entscheidung|decision|weil|begruendung|rationale|stattdessen|verworfen)/i;
  const journals = OWN_DOCS.filter((d) => /(JOURNAL|DECISION|ADR|CHANGELOG)/i.test(path.basename(d.rel)));
  const withWhy = journals.filter((d) => WHY.test(read(d.rel)));
  if (!journals.length) {
    findings.push(finding('decisions', 'medium', 0.75,
      'No place where decisions are recorded with their reasoning',
      'In six months there is no answering why something was built this way. Rejected approaches then get tried a second time.',
      'A journal with three to five lines a day is enough: what was decided, and why.'));
  } else if (!withWhy.length) {
    findings.push(finding('decisions', 'low', 0.7,
      'What happened is recorded, but not why',
      'The what is in the history anyway. The why is what is worth having, and that is exactly what is missing.',
      'Write half a sentence of reasoning alongside every decision.'));
  }
  dim('decisions', 'Knowledge', 'Decision memory', worst(findings),
    `${journals.length} journal files, ${withWhy.length} with reasoning`, findings);
})();

// =========================================================== 9. Life cycle

(function lifecycle() {
  const findings = [];
  // bewusst eng: "slide-1.html" und "2026-07-20.md" sind KEINE Versionsspuren
  const VERSIONED = /((^|[ _\-])(final|fertig|endgueltig|neu|new|alt|old|kopie|copy|backup|test)|[ _\-]v\d+|\(\d+\)|\s\d+)\.[a-z0-9]{2,4}$/i;
  const versioned = FILES.filter((f) => !f.dir && !ARCHIVE.test('/' + f.rel) && VERSIONED.test(path.basename(f.rel)));
  if (versioned.length > 5) {
    findings.push(finding('lifecycle', 'medium', 0.75,
      `${versioned.length} files carry version markers in their name`,
      'With "final" and "new" nobody can tell which one counts any more. Overwriting and duplicated work follow.',
      'Name results by date rather than by version, and move superseded ones to the archive.',
      { examples: versioned.slice(0, 8).map((v) => v.rel) }));
  }
  const byBase = new Map();
  for (const f of FILES) {
    if (f.dir || ARCHIVE.test('/' + f.rel)) continue;
    const b = path.basename(f.rel).toLowerCase();
    if (/^(readme|index|claude|__init__|package)\./.test(b)) continue;
    if (!byBase.has(b)) byBase.set(b, []);
    byBase.get(b).push(f.rel);
  }
  const clones = [...byBase.entries()].filter(([, v]) => v.length > 1);
  if (clones.length > 2) {
    findings.push(finding('lifecycle', 'low', 0.7,
      `${clones.length} file names occur in more than one place`,
      'Same name, two places: sooner or later somebody edits the wrong copy.',
      'Einen Ort zur Wahrheit machen.',
      { examples: clones.slice(0, 5).map(([k, v]) => ({ name: k, at: v })) }));
  }
  dim('lifecycle', 'Craft', 'Life cycle', worst(findings),
    `${versioned.length} version markers, ${clones.length} duplicate names`, findings);
})();

// =========================================================== 10. Backup

(function backup() {
  const findings = [];
  const origin = originUrl();
  let dirty = [], lastPush = null, hasGit = false;
  try {
    execSync('git rev-parse --git-dir', { cwd: ROOT, stdio: 'ignore' });
    hasGit = true;
    dirty = execSync('git status --porcelain', { cwd: ROOT, stdio: ['ignore', 'pipe', 'ignore'], maxBuffer: 1e8 })
      .toString().split('\n').filter(Boolean);
    lastPush = execSync('git log -1 --format=%ct', { cwd: ROOT, stdio: ['ignore', 'pipe', 'ignore'] }).toString().trim();
  } catch { /* kein Repo */ }

  // Ein Unterordner eines groesseren Repos ist gesichert, nur eben nicht selbst.
  let parentRepo = null;
  if (hasGit && !origin) {
    try {
      const top = execSync('git rev-parse --show-toplevel', { cwd: ROOT, stdio: ['ignore', 'pipe', 'ignore'] }).toString().trim();
      if (path.resolve(top) !== ROOT) parentRepo = path.relative(path.dirname(ROOT), top) || top;
    } catch {}
  }

  if (parentRepo) {
    dim('backup', 'Craft', 'Backup', 'ok', `backed up through the parent repo`, [],
      'This folder has no git of its own but sits inside a repo. Its backup depends on the remote of that repo.');
    return;
  }
  if (!hasGit) {
    findings.push(finding('backup', 'high', 0.9,
      'No git in this folder',
      'There is no way back. One wrong move or one dead disk takes everything with it.',
      'git init, then create a private remote.'));
  } else if (!origin) {
    findings.push(finding('backup', 'high', 0.9,
      'git is there, but no remote is set',
      'The history exists only on this machine. That is not a backup.',
      'Create a private remote and push once.'));
  } else {
    const ageDays = lastPush ? days(parseInt(lastPush, 10) * 1000) : null;
    if (ageDays !== null && ageDays > 14) {
      findings.push(finding('backup', 'medium', 0.85,
        `Der letzte Commit ist ${ageDays} Tage her`,
        'Alles seither existiert nur lokal.',
        'Commit and push.'));
    }
    if (dirty.length > 60) {
      findings.push(finding('backup', 'medium', 0.75,
        `${dirty.length} files are uncommitted`,
        'At this volume there is no telling deliberate work from debris.',
        'Commit in batches, or ignore what does not belong in the repo.'));
    }
  }
  dim('backup', 'Craft', 'Backup', worst(findings),
    hasGit ? (origin ? `remote set, ${dirty.length} outstanding` : 'no remote') : 'no git', findings);
})();

// =========================================================== 11. Code quality

// Hier wird bewusst NICHT der Code gelesen. Eine echte Code-Review ist teuer und gehoert
// pro Repo angestossen, nicht als Nebenprodukt eines Ordner-Audits ueber 25 Repos.
// Gemessen wird, was mechanisch und billig zu haben ist und trotzdem etwas aussagt:
// laesst sich das Repo aufgreifen (README), ist Arbeit ungesichert, ruht es.
(function code() {
  if (!NESTED_REPOS.length) {
    dim('code', 'Craft', 'Code quality', 'unknown', 'no repos in the folder', [],
      'Only applies to folders that contain code.');
    return;
  }
  const findings = [];
  const repos = NESTED_REPOS.slice(0, 25).map((rel) => {
    const full = path.join(ROOT, rel);
    const has = (d) => { try { return fs.existsSync(path.join(full, d)); } catch { return false; } };
    let dirty = 0, ageDays = null;
    try {
      dirty = execSync('git status --porcelain', { cwd: full, stdio: ['ignore', 'pipe', 'ignore'], maxBuffer: 1e7 })
        .toString().split('\n').filter(Boolean).length;
      const ct = execSync('git log -1 --format=%ct', { cwd: full, stdio: ['ignore', 'pipe', 'ignore'] }).toString().trim();
      if (ct) ageDays = days(parseInt(ct, 10) * 1000);
    } catch { /* leeres oder kaputtes Repo */ }
    return {
      rel, dirty, ageDays,
      readme: has('README.md') || has('readme.md') || has('README.rst'),
      tests: has('tests') || has('test') || has('__tests__') || has('spec'),
      ci: has('.github/workflows'),
    };
  });

  const noReadme = repos.filter((r) => !r.readme);
  const uncommitted = repos.filter((r) => r.dirty > 0 && (r.ageDays === null || r.ageDays > 14));
  const dormant = repos.filter((r) => r.ageDays !== null && r.ageDays > 180);
  const active = repos.filter((r) => r.ageDays !== null && r.ageDays <= 30);

  if (uncommitted.length) {
    findings.push(finding('code', 'medium', 0.85,
      `${uncommitted.length} repos carry uncommitted work, untouched for over two weeks`,
      'Work started that is neither finished nor backed up. Next time someone picks it up, there is no telling whether it was an experiment or the state of things.',
      'Commit or discard; one short look per repo.',
      { repos: uncommitted.slice(0, 8).map((r) => ({ repo: r.rel, offen: r.dirty })) }));
  }
  if (noReadme.length && active.length) {
    const hits = noReadme.filter((r) => r.ageDays !== null && r.ageDays <= 90);
    if (hits.length) {
      findings.push(finding('code', 'low', 0.75,
        `${hits.length} active repos have no README`,
        'Whoever opens it in three months has to work out from the code what it was for. That goes for Claude too.',
        'Five lines are enough: what it is for, how to start it, where the rest lives.',
        { repos: hits.slice(0, 8).map((r) => r.rel) }));
    }
  }
  if (dormant.length > repos.length / 2) {
    findings.push(finding('code', 'low', 0.7,
      `${dormant.length} of ${repos.length} repos have been dormant for over six months`,
      'Dormant is fine, invisible is not: they are read on every search and blur the overall picture.',
      'Move dormant repos to the archive, so only what is running stays up front.'));
  }

  dim('code', 'Craft', 'Code quality', worst(findings),
    `${repos.length} Repos, ${active.length} aktiv, ${dormant.length} ruhend`, findings,
    'The code itself is not read here. For a real judgement on a single repo, run /security-review or /code-review inside it.');
})();

// ---------------------------------------------------------------- Ausgabe

const result = {
  generatedAt: new Date(NOW).toISOString(),
  root: ROOT,
  profile: { present: PROFILE.present, kind: PROFILE.kind, team: PROFILE.team,
             tools: PROFILE.tools, painpoints: PROFILE.painpoints, channels: PROFILE.channels },
  usage: { available: USAGE.available, sessions: USAGE.sessions, windowDays: USAGE.windowDays,
           skills: USAGE.skills, bins: USAGE.bins, mcp: USAGE.mcp },
  dimensions: dims,
  judgement: null,      // wird vom /audit-Skill gefüllt
};

if (args.includes('--render')) {
  process.stdout.write(renderFragment());
} else if (args.includes('--json')) {
  process.stdout.write(JSON.stringify(result, null, 2));
} else {
  const outPath = path.join(ROOT, 'context', 'audit.json');
  try {
    fs.mkdirSync(path.dirname(outPath), { recursive: true });
    fs.writeFileSync(outPath, JSON.stringify(result, null, 2));
    process.stderr.write(`written: ${outPath}\n`);
  } catch (e) { process.stderr.write(`could not write (${e.message}), use --json\n`); }
  for (const d of dims) {
    process.stderr.write(`${d.level.padEnd(8)} ${d.label.padEnd(26)} ${d.metric}\n`);
    for (const f of d.findings) process.stderr.write(`         · ${f.what}\n`);
  }
}

// Das Fragment für den Dashboard-Tab: dieselben KPI-Kacheln wie die Setup-Uebersicht.
function renderFragment() {
  let data = result;
  try { data = JSON.parse(fs.readFileSync(path.join(ROOT, 'context', 'audit.json'), 'utf8')); } catch {}
  if (!data || !data.dimensions) {
    return '<div class="ivempty">No audit has run yet. Say <code>/audit</code> in chat and the result appears here.</div>';
  }
  // Elf gleich grosse Kacheln behandeln "alles in Ordnung" und "hier musst du ran"
  // als gleich wichtig, und eine geoeffnete Kachel sprengt die Rasterordnung. Beides
  // war derselbe Denkfehler: das hier sind Textbefunde, keine Zahlen zum Ueberfliegen.
  // Jetzt eine Liste nach Dringlichkeit — und was in Ordnung ist, bekommt EINE ruhige
  // Zeile statt fuenf Karten, weil es niemand einzeln lesen will. 23.07.
  const esc2 = esc;
  const samples = (f) => {
    const s = f.evidence && f.evidence.samples;
    if (!Array.isArray(s) || !s.length) return '';
    // The raw signatures are the evidence. "5 repeated steps" without the steps is the
    // generic claim nobody can act on — here they are concrete, with a count.
    return '<ul class="audsamples">' + s.map((x) =>
      `<li><code>${esc2(String(x.pattern || x).slice(0, 78))}</code><span>${esc2(String(x.count || ''))}${x.count ? '×' : ''}</span></li>`
    ).join('') + '</ul>';
  };
  const findingRows = (d) => d.findings.length
    ? d.findings.map((f) => `<div class="audfind"><b>${esc2(f.what)}</b>`
        + `<p>${esc2(f.why)}</p>${samples(f)}<p class="audfix">${esc2(f.fix)}</p></div>`).join('')
    : `<div class="audfind"><p>${esc2(d.note || 'Nichts gefunden.')}</p></div>`;
  const row = (d) => `<details class="audrow lvl-${esc2(d.level)}"><summary>`
    + `<span class="audlvl">${d.level === 'act' ? 'handeln' : 'beobachten'}</span>`
    + `<span class="audname">${esc2(d.label)}</span>`
    + `<span class="audmetric">${esc2(d.metric)}</span>`
    + `<span class="audcount">${d.findings.length}</span></summary>`
    + `<div class="audbody">${findingRows(d)}</div></details>`;
  const cls = { ok: 'ok', watch: 'part', act: 'part', unknown: 'none' };
  // Die grosse Zahl war die ANZAHL DER BEFUNDE und las sich wie eine Note: "1 Security"
  // sah schlechter aus als ein Haken, hiess aber nur "ein Befund". Jetzt fuehrt die Stufe,
  // die Befundzahl steht als Abzeichen daneben. 23.07.
  const lvl = { ok: 'in Ordnung', watch: 'beobachten', act: 'handeln', unknown: 'not measurable' };
  // Handlungsbedarf zuerst, "not measurable" zuletzt. Eine alphabetische oder zufaellige
  // Reihenfolge zwingt jeden dazu, elf Kacheln zu lesen, um die eine zu finden, die zaehlt.
  const rank = { act: 0, watch: 1, ok: 2, unknown: 3 };
  const tiles = [...data.dimensions].sort((a, b) => (rank[a.level] ?? 9) - (rank[b.level] ?? 9)).map((d) => {
    const body = d.findings.length
      ? d.findings.map((f) => `<div class="ivrow"><div class="ivname"><b>${esc(f.what)}</b>`
          + `<span class="inv-badge${f.severity === 'high' ? '' : ' xref'}">${esc(f.severity)}</span></div>`
          + `<p>${esc(f.why)}</p><p><b>${esc(f.fix)}</b></p></div>`).join('')
      : `<div class="ivempty">${esc(d.note || 'Nichts gefunden.')}</div>`;
    return `<details class="kpi ${cls[d.level] || 'none'}" id="aud-${esc(d.id)}"><summary>`
      + `<span class="kpi-num">${d.level === 'ok' ? '✓' : d.level === 'unknown' ? '–' : d.findings.length}</span>`
      + `<span class="kpi-lab">${esc(d.label)}</span>`
      + `<span class="kpi-sub">${esc(lvl[d.level] || d.level)}${d.metric ? ' · ' + esc(d.metric) : ''}</span></summary>`
      + `<div class="kpi-body">${body}</div></details>`;
  }).join('');

  // Der Gesamtstand als EINE Zahl, und zwar eine zaehlbare: wie viele der bewerteten
  // Dimensionen stehen auf "in Ordnung". Keine erfundene Note, keine Gewichtung, die
  // niemand nachrechnen kann — "not measurable" faellt aus dem Nenner, sonst wuerde ein
  // fehlender Beleg wie ein Mangel aussehen.
  const judged = data.dimensions.filter((d) => d.level !== 'unknown');
  const good = judged.filter((d) => d.level === 'ok').length;
  const act = judged.filter((d) => d.level === 'act').length;
  const unknown = data.dimensions.length - judged.length;
  const pct = judged.length ? Math.round((good / judged.length) * 100) : 0;
  const scoreSub = `${good} of ${judged.length} judged dimensions are fine`
    + (act ? `, ${act} needing action` : '')
    + (unknown ? `, ${unknown} not measurable` : '');
  const score = `<details class="kpi ${pct === 100 ? 'ok' : 'part'} wide" id="aud-score"><summary>`
    + `<span class="kpi-num">${pct}%</span>`
    + `<span class="kpi-lab">Gesamtstand</span>`
    + `<span class="kpi-sub">${esc(scoreSub)}</span>`
    + `<span class="kpi-bar" aria-hidden="true"><i style="width:${pct}%"></i></span></summary>`
    + `<div class="kpi-body"><div class="ivempty">The number is a count, not a grade: how many dimensions sit at "fine". What to do about it is in the tiles below, the ones needing action first.</div></div></details>`;

  const byLevel = (lv) => data.dimensions.filter((d) => d.level === lv);
  const acts = byLevel('act');
  const watches = byLevel('watch');
  const oks = byLevel('ok');
  const unknowns = byLevel('unknown');

  const group = (title, sub, rows) => rows.length
    ? `<h4 class="audgrp">${esc(title)}<span>${esc(sub)}</span></h4><div class="audlist">${rows}</div>` : '';

  const quiet = (title, dims, hint) => dims.length
    ? `<div class="audquiet"><b>${esc(title)}</b> ${dims.map((d) => esc(d.label)).join(' · ')}`
      + `<p>${esc(hint)}</p></div>` : '';

  const stamp = new Date(data.generatedAt).toLocaleDateString('en-GB');
  return `<p class="sec-sub">As of ${esc(stamp)}; this does not refresh on its own. To run again: <code>/audit</code> in chat.</p>`
    + `<div class="kpigrid">${score}</div>`
    + group('Hier musst du ran', `${acts.length} of ${data.dimensions.length}`, acts.map(row).join(''))
    + group('Im Auge behalten', `${watches.length} of ${data.dimensions.length}`, watches.map(row).join(''))
    + quiet('In Ordnung:', oks, 'Nothing to do. Expanded, this would only say that everything is fine.')
    + quiet('Nicht messbar:', unknowns, 'No evidence available. That is a limit of the audit, not a fault in your folder.');
}

// --- Selbstpruefung:  node reference/scripts/workspace-audit.js --selftest
if (args.includes('--selftest')) {
  const assert = require('assert');
  assert.ok(dims.length >= 10, `mindestens zehn Dimensionen erwartet, ${dims.length} gefunden`);
  assert.ok(dims.every((d) => ['ok', 'watch', 'act', 'unknown'].includes(d.level)), 'ungueltiges level');
  assert.ok(dims.every((d) => d.group && d.label && d.metric), 'dimension without a group, label or metric');
  const all = dims.flatMap((d) => d.findings);
  assert.ok(all.every((f) => f.confidence >= 0.7), 'finding slipped through below the confidence threshold');
  assert.ok(all.every((f) => f.what && f.why && f.fix), 'finding without a what/why/fix');
  assert.ok(!JSON.stringify(result).includes('undefined'), 'undefined im Ergebnis');
  const frag = renderFragment();
  assert.ok(frag.includes('kpigrid') || frag.includes('ivempty'), 'Fragment leer');
  console.error(`ok, ${dims.length} Dimensionen, ${all.length} Befunde, ${USAGE.sessions} Sessions ausgewertet`);
}
