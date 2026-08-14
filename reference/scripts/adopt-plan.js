#!/usr/bin/env node
// Übernahme-Planer: schlägt vor, wie ein BESTEHENDER Ordner in die Workspace-Struktur
// kommt — und fasst dabei nichts an. Das ist die erste von zwei Hälften; das Ausführen
// ist ein eigener Schritt mit eigenem Rückweg.
//
//   node reference/scripts/adopt-plan.js --root <pfad> [--json]
//
// Die Leitplanken, aus dem Pre-Mortem abgeleitet (was schiefgeht, geht SO schief):
//  1. Nichts wird geraten. Was nicht sicher zuzuordnen ist, kommt auf die Fragen-Liste.
//  2. Eine bestehende CLAUDE.md wird NIE überschrieben, sie wird zusammengeführt.
//  3. Verschieben bricht Verweise. Jeder Vorschlag prüft, ob Scripts, Symlinks oder
//     Dokumente auf den Pfad zeigen — genau daran ist am 22.07. der Morning-Digest gestorben.
//  4. Ein Ordner, der schon am richtigen Platz ist, taucht als "fine" auf, nicht als Arbeit.
//
// ponytail: reine Analyse, kein Modell, keine Schreibvorgänge. Das Urteil über die
// Fragen-Liste macht der /adopt-Skill.

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const args = process.argv.slice(2);
const argOf = (n) => { const i = args.indexOf(n); return i >= 0 ? args[i + 1] : null; };
const ROOT = path.resolve(argOf('--root') || process.cwd());

// Die Zielstruktur. Bewusst als Beschreibung, nicht als Prüfliste: ein Ordner muss nicht
// so heißen, er muss diese Rolle erfüllen.
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

// Zählt, wie viel Inhalt in einem Ordner steckt — ein leerer Ordner ist keine Arbeit.
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

// Leitplanke 3: Wer zeigt auf diesen Pfad? Verschieben ohne das zu wissen ist fahrlässig.
// EIN Durchlauf über die relevanten Textdateien, nicht einer je Eintrag — sonst dauert der
// Plan auf einem gewachsenen Ordner Minuten und wird nie benutzt.
// In Node gehen statt ueber `find`: das POSIX-`find` mit `\( -name ... \)` und `head`
// existiert auf Windows nicht. Vorher fiel der Aufruf dort still in den catch, `files`
// blieb leer, und der Plan behauptete fuer JEDEN Ordner "niemand verweist darauf" —
// also ausgerechnet die Pruefung, die den Umbau absichern soll, sagte immer Entwarnung.
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
  // Verweise von ausserhalb wiegen am schwersten: die brechen still.
  // `checked: false` heisst "hier konnte niemand nachsehen" und ist ausdruecklich NICHT
  // dasselbe wie "es gibt keine". Auf Windows liegen geplante Jobs im Task Scheduler,
  // den dieses Skript nicht liest — dort muss der Plan das sagen statt Entwarnung zu geben.
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

// ---------------------------------------------------------------- Innerhalb der Projekte
// Ein Ordner, dessen Wurzel schon stimmt, ist NICHT automatisch uebernommen: die
// Abweichung sitzt dann eine Ebene tiefer. Am 22.07. im ersten echten Lauf aufgefallen —
// der Plan meldete "11 fine schon, 0 Vorschlaege", waehrend elf von sechzehn Projekten
// `docs/` statt `work/` fuehrten. Blind fuer genau den Fall, fuer den man ihn braucht.
// Bewusst nur SICHTBAR machen, nicht vorschlagen: wie ein gewachsener Projektordner
// heisst, weiss der Nutzer, nicht dieses Script.
// Misst ein einzelnes Projekt. Keine Bewertung, nur Zahlen — das Urteil macht der Skill.
// Eine Konfliktkopie ist NICHT "Name enthaelt 2". Sonst faellt "Seedance 2.0" darunter,
// ein Produktname, und am 22.07. ist genau das passiert: er wurde als Duplikat einsortiert.
// Der Beweis ist die Nachbardatei: "x 2.md" ist nur dann eine Kopie, wenn "x.md" daneben
// liegt. Alles andere ist ein Name, der zufaellig eine Zahl enthaelt.
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

      // Drei Fakten je Projekt, damit der Skill fragen kann statt zu raten:
      // wann zuletzt etwas passiert ist, was lose herumliegt, und ob es Versionsspuren
      // gibt ("angebot final v2"). Bewertet wird hier nichts — nur gemessen.
      const st = scanProject(dir);
      if (st.ruhtTage !== null && st.ruhtTage > 90) out.ruhend.push({ label, tage: st.ruhtTage });
      if (st.lose > 0) out.lose.push({ label, n: st.lose });
      if (st.versionen.length) out.versionen.push({ label, beispiele: st.versionen.slice(0, 3) });
      let subs = [];
      try { subs = fs.readdirSync(dir, { withFileTypes: true }); } catch { continue; }
      for (const sd of subs) {
        if (!sd.isDirectory() || sd.name.startsWith('.') || KNOWN_SUB.has(sd.name)) continue;
        // Ein Unterordner mit eigenem .git ist ein fremdes Repo — Kundencode, ein Produkt,
        // ein geklonter Fremdstand. Der wird NIE als Strukturabweichung gemeldet und nie
        // angefasst: er hat eine eigene Historie und oft einen anderen Eigentuemer.
        if (hasGit(path.join(dir, sd.name))) { out.eigeneRepos.push(label + '/' + sd.name); continue; }
        if (!out.fremdeOrdner.has(sd.name)) out.fremdeOrdner.set(sd.name, []);
        out.fremdeOrdner.get(sd.name).push(label);
      }
    }
  }
  return out;
}

// ---------------------------------------------------------- inputs / work / outputs
// Trennt in einem bestehenden work/ (oder docs/), was ERHALTEN wurde von dem, was der
// Nutzer selbst gemacht hat. Am 22.07. an echten Daten entwickelt, drei Anlaeufe:
//
//   1. Zeitstempel ("nie bearbeitet = erhalten") — TOT. Ein einziger Ordner-Umzug setzt
//      Erstell- und Aenderungszeit gleich, danach sieht alles unbearbeitet aus.
//   2. git-Historie ("einmal hinzugefuegt = erhalten") — TOT. Struktur-Commits fassen
//      alle Dateien gleichzeitig an, die Zahl ist danach fuer jede Datei dieselbe.
//   3. Format + Name, geurteilt auf der ERSTEN Ebene unter work/ — traegt.
//
// Die Ebene ist der eigentliche Trick. Pro Datei entstehen Hunderte Fragen; pro Blatt-
// Ordner immer noch dutzende und lauter Unsinn (jede fremde CSS-Datei einer geklonten
// Website galt als "written by hand"). Ein Mensch denkt in der ersten Ebene: "der
// website-Ordner ist eine Kopie, ernaehrung ist ein Vorhaben". Genau da wird geurteilt.
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

  // Ein Symlink ins Leere ist kein raetselhafter Eintrag, sondern ein bekannter Defekt.
  // Vorher landete er unter "Zweck nicht erkennbar" — dieselbe Datei, die workspace-audit.js
  // korrekt als Fehler meldet. Zwei Skripte desselben Pakets duerfen nicht verschieden urteilen.
  if (e.link && !fs.existsSync(e.full)) {
    return { verdict: 'question', target: null,
      why: 'Dead link: the target does not exist (any more). Decide before the move whether it can go or has to be repaired.' };
  }

  // Buchhaltung bleibt liegen, immer. Dieses System haelt Arbeitsstand, es ist keine
  // Ablage fuer Rechnungen — dort haengen Aufbewahrungsfristen und der Zugriff des
  // Steuerberaters dran. Kein Ziel vorzuschlagen ist hier die richtige Antwort, nicht
  // eine fehlende. Siehe WHAT-THIS-SYSTEM-DOES.md.
  if (e.dir && /^(rechnung|buchhalt|invoic|bookkeep|accounting|finanz|belege|steuer|datev|lexoffice)/i.test(e.name)) {
    return { verdict: 'fine', target: e.name,
      why: 'Accounting. Stays where it is: this system holds work in progress, not invoices.' };
  }

  // Maschinerie bleibt liegen. Alles mit Punkt am Anfang und die bekannten Konfig-Dateien
  // sind Werkzeug, nicht Inhalt — sie zu verschieben bricht das, was den Ordner bedient.
  // Die Regel ist absichtlich breit: lieber etwas liegen lassen als etwas kaputtziehen.
  const CONFIG = /^(package(-lock)?\.json|pnpm-lock\.yaml|yarn\.lock|skills-lock\.json|Makefile|\.?env(\..+)?|tsconfig\.json|requirements\.txt|pyproject\.toml)$/i;
  if (e.name.startsWith('.') || CONFIG.test(e.name)) {
    return { verdict: 'fine', target: e.name,
      why: 'Machinery or configuration. Stays where it is, or the folder stops working.' };
  }

  // Schon am Platz?
  if (e.dir && TARGET[e.name]) return { verdict: 'fine', target: e.name, why: TARGET[e.name] };
  // Ein Symlink auf eine Datei, die es hier schon gibt, ist ein Zweitname, kein zweiter
  // Inhalt. AGENT.md -> CLAUDE.md ist der Normalfall (andere Werkzeuge lesen den anderen
  // Namen). Ihn zum Zusammenfuehren vorzuschlagen hiesse, eine Datei in sich selbst zu
  // mergen — am 22.07. im ersten echten Lauf aufgefallen.
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
    return { verdict: 'suggestion', target: `projects/<gruppe>/${slug(e.name)}/code/`,
      why: 'A repo of its own with its own history. It moves as a whole, and the history is left untouched.' };
  }
  if (e.dir && (fs.existsSync(path.join(e.full, 'package.json')) || fs.existsSync(path.join(e.full, 'pyproject.toml')))) {
    return { verdict: 'suggestion', target: `projects/<gruppe>/${slug(e.name)}/code/`,
      why: 'Looks like code (package.json or pyproject.toml) but has no git. Check it is backed up before moving it.' };
  }

  // Dokumente und Material
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

  // Verbleibende Ordner: nach Inhalt entscheiden, nicht nach Namen
  const w = weigh(e.full);
  if (w.files === 0) return { verdict: 'question', target: null, why: 'Folder is empty. Remove it, or is it reserved for something?' };
  if (w.docs >= w.files * 0.6) {
    return { verdict: 'suggestion', target: `projects/<gruppe>/${slug(e.name)}/`,
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
      out.ungeprueft = 'Scheduled jobs outside this folder could not be checked (no ~/Library/LaunchAgents; on Windows this lives in Task Scheduler). Have a look yourself before moving anything.';
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
      if (p.ungeprueft) L(`     ? ${p.ungeprueft}`);
    }
    L('');
  }
  if (groups.question.length) {
    L('NEEDS YOUR ANSWER (nothing is guessed here)');
    for (const p of groups.question) L(`  ${p.name}  —  ${p.why}`);
    L('');
  }
  // Herkunfts-Trennung: nur auf ausdrueckliche Anfrage, sie kostet einen Durchlauf je Projekt.
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
