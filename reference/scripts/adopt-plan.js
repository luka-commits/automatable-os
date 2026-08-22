#!/usr/bin/env node
// Adoption planner: proposes how an EXISTING folder moves into the workspace structure,
// and touches nothing while doing it. This is the first of two halves; carrying it out is
// a separate step with its own way back.
//
//   node reference/scripts/adopt-plan.js --root <path> [--json]
//
// The guardrails, derived from a pre-mortem (what goes wrong goes wrong THIS way):
//  1. Nothing is guessed. Anything that cannot be placed confidently goes on the questions list.
//  2. An existing CLAUDE.md is NEVER overwritten, it is merged.
//  3. Moving breaks references. Every proposal checks whether scripts, symlinks or
//     documents point at the path — that is exactly how a morning digest once died.
//  4. A folder already in the right place shows up as "fine", not as work.
//
// Pure analysis, no model, no writes. The judgement on the questions list is the
// /adopt skill's job.

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const args = process.argv.slice(2);
const argOf = (n) => { const i = args.indexOf(n); return i >= 0 ? args[i + 1] : null; };
const ROOT = path.resolve(argOf('--root') || process.cwd());

// The target structure. Deliberately a description rather than a checklist: a folder does
// not have to carry this name, it has to fill this role.
const TARGET = {
  context: 'State: what currently holds — projects, tasks, history',
  projects: 'One folder per project, holding inputs/ work/ outputs/ and code/ where needed',
  reference: 'What does not change: tools, rules, reference material',
  inbox: 'Drop zone for anything unprocessed',
};
const JUNK = /^(node_modules|\.DS_Store|\.venv|venv|__pycache__|dist|build|\.next|\.cache|\.turbo)$/;
const MEDIA = /\.(png|jpe?g|gif|mp4|mov|heic|webp|svg|pdf|docx?|xlsx?|pptx?|key|numbers|pages)$/i;
const STATE_DOC = /(STATUS|TODO|NOTES?|JOURNAL|PROJECTS|ROADMAP|NEXT|AUFGABEN|NOTIZEN)/i;

const rel = (p) => path.relative(ROOT, p) || '.';
const isDir = (p) => { try { return fs.statSync(p).isDirectory(); } catch { return false; } };
const hasGit = (p) => fs.existsSync(path.join(p, '.git'));

// ---------------------------------------------------------------- Bestandsaufnahme

function topLevel() {
  let entries = [];
  try { entries = fs.readdirSync(ROOT, { withFileTypes: true }); } catch { return []; }
  return entries.map((e) => {
    const full = path.join(ROOT, e.name);
    const link = e.isSymbolicLink();
    return {
      name: e.name, full, link,
      dir: link ? isDir(full) : e.isDirectory(),
      repo: !link && e.isDirectory() && hasGit(full),
      size: (() => { try { return fs.statSync(full).size; } catch { return 0; } })(),
    };
  });
}

// Counts how much content a folder holds — an empty folder is not work.
function weigh(dir, depth = 3) {
  let files = 0, docs = 0, media = 0;
  const walk = (d, lvl) => {
    let es = [];
    try { es = fs.readdirSync(d, { withFileTypes: true }); } catch { return; }
    for (const e of es) {
      if (JUNK.test(e.name)) continue;
      const full = path.join(d, e.name);
      if (e.isDirectory()) { if (lvl > 0) walk(full, lvl - 1); continue; }
      files++;
      if (/\.md$/i.test(e.name)) docs++;
      if (MEDIA.test(e.name)) media++;
    }
  };
  walk(dir, depth);
  return { files, docs, media };
}

// Guardrail 3: who points at this path? Moving without knowing that is reckless.
// ONE pass over the relevant text files, not one per entry — otherwise the plan takes
// minutes on a folder that has grown, and then nobody runs it.
// Done in Node rather than through `find`: POSIX `find` with `\( -name ... \)` and `head`
// does not exist on Windows. It used to fall silently into the catch there, `files` stayed
// empty, and the plan claimed "nothing references this" for EVERY folder — so the very
// check meant to make the rebuild safe always said all clear.
const REF_EXT = new Set(['.sh', '.plist', '.js', '.ts', '.py', '.json', '.yaml', '.yml', '.md']);
const REF_SKIP = new Set(['node_modules', '.git', '.venv', 'dist', 'build']);
const REF_INDEX = (() => {
  const files = [];
  const walk = (dir, rel, depth) => {
    if (depth > 5 || files.length >= 800) return;
    let entries = [];
    try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch { return; }
    for (const e of entries) {
      if (files.length >= 800) return;
      if (REF_SKIP.has(e.name)) continue;
      const abs = path.join(dir, e.name);
      const r = rel ? rel + '/' + e.name : e.name;
      if (e.isDirectory()) walk(abs, r, depth + 1);
      else if (REF_EXT.has(path.extname(e.name))) files.push(r);
    }
  };
  walk(ROOT, '', 0);
  return { files };
})();

function referrers(name) {
  const inside = [];
  for (const f of REF_INDEX.files) {
    let t = '';
    try {
      const st = fs.statSync(path.join(ROOT, f));
      if (st.size > 300000) continue;
      t = fs.readFileSync(path.join(ROOT, f), 'utf8');
    } catch { continue; }
    if (t.includes(name + '/') || t.includes('/' + name)) inside.push(f.replace(/^\.\//, ''));
    if (inside.length >= 6) break;
  }
  // References from outside weigh most: those break silently.
  // `checked: false` means "nobody could look here" and is explicitly NOT the same as
  // "there are none". On Windows, scheduled jobs live in Task Scheduler, which this script
  // does not read — there the plan has to say so rather than give an all clear.
  const outside = [];
  let checked = false;
  const la = path.join(require('os').homedir(), 'Library', 'LaunchAgents');
  try {
    const entries = fs.readdirSync(la);
    checked = true;
    for (const f of entries) {
      try {
        const t = fs.readFileSync(path.join(la, f), 'utf8');
        if (t.includes(path.join(ROOT, name))) outside.push('~/Library/LaunchAgents/' + f);
      } catch {}
    }
  } catch {}
  return { inside, outside, outsideChecked: checked };
}

// ------------------------------------------------------------------ Inside the projects
// A folder whose root is already correct is NOT automatically adopted: the deviation then
// sits one level down. Found on the first real run — the plan reported "11 already fine,
// 0 suggestions" while eleven of sixteen projects used `docs/` instead of `work/`. Blind
// to exactly the case it exists for.
// Deliberately only made VISIBLE, never proposed: what a grown project folder is called is
// something the user knows and this script does not.
// Measures a single project. No assessment, only numbers — the judgement is the skill's.
// A conflict copy is NOT "the name contains 2". Otherwise "Seedance 2.0" qualifies, which
// is a product name, and that is exactly what once happened: it got filed as a duplicate.
// The proof is the neighbouring file: "x 2.md" is a copy only when "x.md" sits next to it.
// Anything else is a name that happens to contain a number.
const VERSIONSSPUR = /( final| v\d| kopie| copy|\(\d\))\.[a-z0-9]+$/i;
const SYNC_KOPIE = / 2\.[a-z0-9]+$/i;
function istKonfliktkopie(dir, name) {
  if (!SYNC_KOPIE.test(name)) return false;
  const original = name.replace(/ 2(\.[a-z0-9]+)$/i, '$1');
  try { return fs.existsSync(path.join(dir, original)); } catch { return false; }
}
function scanProject(dir) {
  let neuste = 0, lose = 0;
  const versionen = [];
  const walk = (d, lvl) => {
    let es = [];
    try { es = fs.readdirSync(d, { withFileTypes: true }); } catch { return; }
    for (const e of es) {
      if (JUNK.test(e.name) || e.name === '.git') continue;
      const full = path.join(d, e.name);
      if (e.isDirectory()) { if (lvl > 0 && !hasGit(full)) walk(full, lvl - 1); continue; }
      let st; try { st = fs.statSync(full); } catch { continue; }
      if (st.mtimeMs > neuste) neuste = st.mtimeMs;
      if ((VERSIONSSPUR.test(e.name) || istKonfliktkopie(d, e.name)) && versionen.length < 6) versionen.push(e.name);
    }
  };
  walk(dir, 3);
  try {
    lose = fs.readdirSync(dir, { withFileTypes: true })
      .filter((e) => e.isFile() && e.name !== 'README.md' && !e.name.startsWith('.')).length;
  } catch {}
  const ruhtTage = neuste ? Math.floor((Date.now() - neuste) / 86400000) : null;
  return { ruhtTage, lose, versionen };
}

const KNOWN_SUB = new Set(['inputs', 'work', 'outputs', 'code', '_archive']);
function insideProjects() {
  const base = path.join(ROOT, 'projects');
  if (!isDir(base)) return null;
  const out = { projects: 0, ohneReadme: [], fremdeOrdner: new Map(), ohneWork: 0, ohneInputs: 0,
                ruhend: [], lose: [], versionen: [], eigeneRepos: [] };
  const groups = (() => { try { return fs.readdirSync(base, { withFileTypes: true }); } catch { return []; } })();
  for (const g of groups) {
    if (!g.isDirectory() || /^_/.test(g.name)) continue;
    let projs = [];
    try { projs = fs.readdirSync(path.join(base, g.name), { withFileTypes: true }); } catch { continue; }
    for (const pr of projs) {
      if (!pr.isDirectory() || /^_/.test(pr.name)) continue;
      const dir = path.join(base, g.name, pr.name);
      const label = g.name + '/' + pr.name;
      out.projects++;
      if (!fs.existsSync(path.join(dir, 'README.md'))) out.ohneReadme.push(label);
      if (!isDir(path.join(dir, 'work'))) out.ohneWork++;
      if (!isDir(path.join(dir, 'inputs'))) out.ohneInputs++;

      // Three facts per project, so the skill can ask instead of guess: when something
      // last happened, what is lying around loose, and whether there are version markers
      // ("quote final v2"). Nothing is assessed here, only measured.
      const st = scanProject(dir);
      if (st.ruhtTage !== null && st.ruhtTage > 90) out.ruhend.push({ label, tage: st.ruhtTage });
      if (st.lose > 0) out.lose.push({ label, n: st.lose });
      if (st.versionen.length) out.versionen.push({ label, beispiele: st.versionen.slice(0, 3) });
      let subs = [];
      try { subs = fs.readdirSync(dir, { withFileTypes: true }); } catch { continue; }
      for (const sd of subs) {
        if (!sd.isDirectory() || sd.name.startsWith('.') || KNOWN_SUB.has(sd.name)) continue;
        // A subfolder with its own .git is someone else's repo — client code, a product,
        // a cloned third-party checkout. It is NEVER reported as a structural deviation and
        // never touched: it has its own history and often a different owner.
        if (hasGit(path.join(dir, sd.name))) { out.eigeneRepos.push(label + '/' + sd.name); continue; }
        if (!out.fremdeOrdner.has(sd.name)) out.fremdeOrdner.set(sd.name, []);
        out.fremdeOrdner.get(sd.name).push(label);
      }
    }
  }
  return out;
}

// ------------------------------------------------------------ inputs / work / outputs
// Inside an existing work/ (or docs/), separates what was RECEIVED from what the user made
// themselves. Developed against real data, in three attempts:
//
//   1. Timestamps ("never edited = received") — DEAD. A single folder move sets creation
//      and modification time equal, after which everything looks untouched.
//   2. git history ("added once = received") — DEAD. Structural commits touch every file
//      at the same time, so the number is identical for every file afterwards.
//   3. Format + name, judged at the FIRST level under work/ — this one holds.
//
// The level is the actual trick. Per file you get hundreds of questions; per leaf folder
// still dozens and plenty of nonsense (every foreign CSS file of a cloned website counted
// as "written by hand"). A person thinks at the first level: "the website folder is a copy,
// nutrition is a project". That is where the judgement belongs.
const ERH_EXT = new Set(['.pdf','.docx','.doc','.xlsx','.xls','.pptx','.ppt','.vtt','.m4a','.mp3','.wav','.heic','.zip','.eml','.msg']);
const ERH_NAME = /^(original|scan|img[_-]?\d|dsc\d|foto|photo|whatsapp|screenshot|bildschirmfoto)/i;
const EIG_EXT = new Set(['.md','.html','.css','.js','.py','.yaml','.yml','.json','.txt','.sh','.ts']);
const BILD_EXT = new Set(['.png','.jpg','.jpeg','.gif','.svg','.webp']);
const FREMD_MARKER = ['wp-content','wp-includes','node_modules','vendor','_next','wp-json'];
const AUS_DIR = /^(generated|generiert|export|exports|deliverables|final|versand|out)$/i;

function sammle(dir) {
  const st = { files: 0, erh: 0, eig: 0, bild: 0, fremd: false };
  const walk = (d, relPath) => {
    if (FREMD_MARKER.some((m) => relPath.includes(m))) st.fremd = true;
    let es = [];
    try { es = fs.readdirSync(d, { withFileTypes: true }); } catch { return; }
    for (const e of es) {
      if (e.name.startsWith('.') || JUNK.test(e.name)) continue;
      const full = path.join(d, e.name);
      if (e.isDirectory()) { walk(full, relPath + '/' + e.name); continue; }
      const ext = path.extname(e.name).toLowerCase();
      st.files++;
      if (ERH_EXT.has(ext) || ERH_NAME.test(e.name)) st.erh++;
      else if (EIG_EXT.has(ext)) st.eig++;
      else if (BILD_EXT.has(ext)) st.bild++;
    }
  };
  walk(dir, '');
  return st;
}

function provenance(workDir) {
  const out = [];
  let es = [];
  try { es = fs.readdirSync(workDir, { withFileTypes: true }); } catch { return out; }
  for (const e of es) {
    if (e.name.startsWith('.')) continue;
    if (!e.isDirectory()) {
      const ext = path.extname(e.name).toLowerCase();
      out.push({ name: e.name, n: 1,
        urteil: EIG_EXT.has(ext) ? 'work' : (ERH_EXT.has(ext) || ERH_NAME.test(e.name) ? 'inputs' : '?'),
        why: EIG_EXT.has(ext) ? 'written by hand' : 'the format says nothing conclusive' });
      continue;
    }
    const st = sammle(path.join(workDir, e.name));
    let urteil = '?', why = `gemischt: ${st.erh} erhalten, ${st.eig} eigene, ${st.bild} Bilder`;
    if (st.fremd) { urteil = 'inputs'; why = 'heruntergeladene Fremdsache (wp-content, node_modules, vendor)'; }
    else if (AUS_DIR.test(e.name)) { urteil = 'outputs'; why = 'Ordnername sagt: Erzeugnis'; }
    else if (st.files && st.erh / st.files > 0.5) { urteil = 'inputs'; why = `${st.erh} von ${st.files} sind Empfangsformate`; }
    else if (st.eig + st.bild > 0 && st.erh / Math.max(st.files, 1) < 0.15) {
      urteil = 'work'; why = `${st.eig} eigene, ${st.bild} Bilder, ${st.erh} erhalten`; }
    out.push({ name: e.name, n: st.files, urteil, why });
  }
  return out;
}

// ---------------------------------------------------------------- Zuordnung

function classify(e) {
  if (JUNK.test(e.name)) return { verdict: 'ignorieren', why: 'generated, not written' };

  // A symlink into nothing is not a puzzling entry, it is a known defect. It used to land
  // under "purpose not recognisable" — the same file that workspace-audit.js correctly
  // reports as broken. Two scripts from one package must not judge it differently.
  if (e.link && !fs.existsSync(e.full)) {
    return { verdict: 'question', target: null,
      why: 'Dead link: the target does not exist (any more). Decide before the move whether it can go or has to be repaired.' };
  }

  // Accounting stays put, always. This system holds work in progress, it is not a store
  // for invoices — those carry retention periods and an accountant's access. Proposing no
  // destination is the right answer here, not a missing one. See WHAT-THIS-SYSTEM-DOES.md.
  if (e.dir && /^(rechnung|buchhalt|invoic|bookkeep|accounting|finanz|belege|steuer|datev|lexoffice)/i.test(e.name)) {
    return { verdict: 'fine', target: e.name,
      why: 'Accounting. Stays where it is: this system holds work in progress, not invoices.' };
  }

  // Machinery stays put. Everything starting with a dot, and the known config files, are
  // tooling rather than content — moving them breaks whatever operates the folder.
  // The rule is deliberately broad: better to leave something than to pull something apart.
  const CONFIG = /^(package(-lock)?\.json|pnpm-lock\.yaml|yarn\.lock|skills-lock\.json|Makefile|\.?env(\..+)?|tsconfig\.json|requirements\.txt|pyproject\.toml)$/i;
  if (e.name.startsWith('.') || CONFIG.test(e.name)) {
    return { verdict: 'fine', target: e.name,
      why: 'Machinery or configuration. Stays where it is, or the folder stops working.' };
  }

  // Schon am Platz?
  if (e.dir && TARGET[e.name]) return { verdict: 'fine', target: e.name, why: TARGET[e.name] };
  // A symlink to a file that already exists here is a second name, not second content.
  // AGENT.md -> CLAUDE.md is the normal case (other tools read the other name). Proposing
  // it for merging would mean merging a file into itself — found on the first real run.
  if (e.link && /^(CLAUDE|AGENTS?|README)\.md$/i.test(e.name)) {
    let target = null;
    try { target = path.relative(ROOT, fs.realpathSync(e.full)); } catch {}
    return { verdict: 'fine', target: e.name,
      why: `Second name for ${target || 'a file in this folder'}. Stays, so tools find it under either name.` };
  }
  if (/^(CLAUDE|AGENTS?)\.md$/i.test(e.name)) {
    return { verdict: 'merge', target: 'CLAUDE.md',
      why: 'Instructions already exist here. They get added to, never replaced: what is written here was earned.' };
  }
  if (/^README\.md$/i.test(e.name)) return { verdict: 'fine', target: 'README.md', why: 'The entry point of this folder' };

  // Code
  if (e.repo) {
    return { verdict: 'suggestion', target: `projects/${slug(e.name)}/code/`,
      why: 'A repo of its own with its own history. It moves as a whole, and the history is left untouched.' };
  }
  if (e.dir && (fs.existsSync(path.join(e.full, 'package.json')) || fs.existsSync(path.join(e.full, 'pyproject.toml')))) {
    return { verdict: 'suggestion', target: `projects/${slug(e.name)}/code/`,
      why: 'Looks like code (package.json or pyproject.toml) but has no git. Check it is backed up before moving it.' };
  }

  // Documents and material
  if (!e.dir) {
    if (STATE_DOC.test(e.name) && /\.md$/i.test(e.name)) {
      return { verdict: 'suggestion', target: `context/${e.name}`,
        why: 'Carries state (tasks, status, history). State belongs in ONE place, otherwise it drifts.' };
    }
    if (/\.md$/i.test(e.name)) {
      return { verdict: 'question', target: null,
        why: 'A document in the root. Does it belong to a project, or is it reference material?' };
    }
    if (MEDIA.test(e.name)) {
      return { verdict: 'suggestion', target: 'inbox/',
        why: 'Loose material. From the inbox it gets assigned to a project instead of sitting in the root.' };
    }
    return { verdict: 'question', target: null, why: 'File in the root, purpose not recognisable.' };
  }

  // Remaining folders: decide by content, not by name
  const w = weigh(e.full);
  if (w.files === 0) return { verdict: 'question', target: null, why: 'Folder is empty. Remove it, or is it reserved for something?' };
  if (w.docs >= w.files * 0.6) {
    return { verdict: 'suggestion', target: `projects/${slug(e.name)}/`,
      why: `Mostly documents (${w.docs} of ${w.files}). Looks like a project.` };
  }
  return { verdict: 'question', target: null,
    why: `Mixed contents (${w.files} files, of which ${w.docs} documents and ${w.media} media). Placing this needs your answer.` };
}

const slug = (s) => s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

// ---------------------------------------------------------------- Ausgabe

const entries = topLevel().filter((e) => !/^\.(DS_Store|localized)$/.test(e.name));
const plan = entries.map((e) => {
  const c = classify(e);
  const out = { name: e.name, typ: e.dir ? (e.repo ? 'repo' : 'folder') : 'file', ...c };
  if (c.verdict === 'suggestion') {
    const r = referrers(e.name);
    if (r.inside.length || r.outside.length) {
      out.verweise = r;
      out.warnung = r.outside.length
        ? 'A job outside this folder points here. Moving it breaks that job SILENTLY. Update the job first, then move.'
        : 'Documents or scripts name this path. Update them after the move.';
    }
    if (!r.outsideChecked) {
      out.unchecked = 'Scheduled jobs outside this folder could not be checked (no ~/Library/LaunchAgents; on Windows this lives in Task Scheduler). Have a look yourself before moving anything.';
    }
  }
  return out;
});

const groups = {
  fine: plan.filter((p) => p.verdict === 'fine'),
  suggestion: plan.filter((p) => p.verdict === 'suggestion'),
  question: plan.filter((p) => p.verdict === 'question'),
  merge: plan.filter((p) => p.verdict === 'merge'),
  ignorieren: plan.filter((p) => p.verdict === 'ignorieren'),
};

const result = {
  root: ROOT,
  bereitsStrukturiert: groups.fine.length,
  zuVerschieben: groups.suggestion.length,
  offeneFragen: groups.question.length,
  istRepo: hasGit(ROOT),
  plan,
};

if (args.includes('--json')) {
  process.stdout.write(JSON.stringify(result, null, 2));
} else {
  const L = (s) => process.stdout.write(s + '\n');
  L(`Adoption plan for ${ROOT}`);
  L(`${groups.fine.length} already fine · ${groups.suggestion.length} suggestions · ${groups.question.length} questions for you\n`);
  if (groups.fine.length) {
    L('ALREADY FINE');
    for (const p of groups.fine) L(`  ${p.name}  —  ${p.why}`);
    L('');
  }
  if (groups.merge.length) {
    L('MERGE');
    for (const p of groups.merge) L(`  ${p.name}  —  ${p.why}`);
    L('');
  }
  if (groups.suggestion.length) {
    L('VORSCHLAG ZUM VERSCHIEBEN');
    for (const p of groups.suggestion) {
      L(`  ${p.name}  →  ${p.target}`);
      L(`     ${p.why}`);
      if (p.warnung) L(`     ⚠ ${p.warnung}`);
      if (p.verweise && p.verweise.outside.length) L(`       ausserhalb: ${p.verweise.outside.join(', ')}`);
      if (p.verweise && p.verweise.inside.length) L(`       nennen den Pfad: ${p.verweise.inside.slice(0, 4).join(', ')}`);
      if (p.unchecked) L(`     ? ${p.unchecked}`);
    }
    L('');
  }
  if (groups.question.length) {
    L('NEEDS YOUR ANSWER (nothing is guessed here)');
    for (const p of groups.question) L(`  ${p.name}  —  ${p.why}`);
    L('');
  }
  // Provenance split: only on explicit request, it costs one pass per project.
  const hp = argOf('--provenance');
  if (hp) {
    const wd = path.resolve(ROOT, hp);
    L(`HERKUNFT IN ${path.relative(ROOT, wd) || '.'}`);
    L('  Was wurde erhalten (inputs), was ist eigene Arbeit (work), was ging raus (outputs)?');
    L('');
    const rows = provenance(wd);
    const question = rows.filter((r) => r.urteil === '?');
    for (const r of rows.filter((x) => x.urteil !== '?')) {
      L(`  ${r.urteil.padEnd(8)} ${r.name.padEnd(28)} ${String(r.n).padStart(4)} Dateien — ${r.why}`);
    }
    if (question.length) {
      L('');
      L('  NEEDS YOUR ANSWER:');
      for (const r of question) L(`    ${r.name.padEnd(28)} ${String(r.n).padStart(4)} Dateien — ${r.why}`);
    }
    L('');
    L('None of this has happened. This run only reads.');
    process.exit(0);
  }

  const inner = insideProjects();
  if (inner && inner.projects) {
    L('INSIDE THE PROJECTS (for information only, nothing suggested here)');
    L(`  ${inner.projects} Projekte · ${inner.projects - inner.ohneWork} mit work/ · ${inner.projects - inner.ohneInputs} mit inputs/`);
    if (inner.ohneReadme.length) L(`  ohne README: ${inner.ohneReadme.join(', ')}`);
    const wiederkehrend = [...inner.fremdeOrdner.entries()].filter(([, v]) => v.length >= 3)
      .sort((a, b) => b[1].length - a[1].length);
    for (const [name, wo] of wiederkehrend) {
      L(`  "${name}/" appears in ${wo.length} projects: a convention of your own that the schema does not know.`);
      L(`     ${wo.slice(0, 6).join(', ')}${wo.length > 6 ? ' and more' : ''}`);
    }
    if (inner.eigeneRepos.length) {
      L(`  ${inner.eigeneRepos.length} eigene Repos in Projekten — unberuehrt, eigene Historie:`);
      L(`     ${inner.eigeneRepos.slice(0, 6).join(', ')}${inner.eigeneRepos.length > 6 ? ' and more' : ''}`);
    }
    if (inner.ruhend.length) {
      L(`  seit ueber 90 Tagen ohne Aenderung (Archiv-Kandidaten, nur zur Frage):`);
      for (const r of inner.ruhend.slice(0, 8)) L(`     ${r.label} — ${r.tage} Tage`);
    }
    if (inner.lose.length) {
      L(`  loose files directly in the project folder (they belong in work/ or inputs/):`);
      for (const r of inner.lose.slice(0, 8)) L(`     ${r.label} — ${r.n}`);
    }
    if (inner.versionen.length) {
      L(`  Versionsspuren im Dateinamen (final, v2, Kopie):`);
      for (const r of inner.versionen.slice(0, 6)) L(`     ${r.label} — ${r.beispiele.join(', ')}`);
    }
    if (!wiederkehrend.length && !inner.ohneReadme.length && !inner.ruhend.length
        && !inner.lose.length && !inner.versionen.length) L('  No recurring deviation found.');
    L('');
  }
  L('None of this has happened. This run only reads.');
}

// --- Selbstprüfung:  node reference/scripts/adopt-plan.js --selftest
if (args.includes('--selftest')) {
  const assert = require('assert');
  assert.ok(plan.length > 0, 'nothing recorded');
  assert.ok(plan.every((p) => p.verdict && p.why), 'entry without a judgement or a reason');
  assert.ok(plan.every((p) => p.verdict !== 'suggestion' || p.target), 'Vorschlag ohne Ziel');
  assert.ok(!JSON.stringify(result).includes('undefined'), 'undefined im Ergebnis');
  console.error(`ok, ${plan.length} entries, ${groups.suggestion.length} suggestions, ${groups.question.length} questions`);
}
