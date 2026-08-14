#!/usr/bin/env node
// Prints the {{AUSSTATTUNG}} fragment for the dashboard: seven category blocks,
// always all seven, always in this order. Skills, CLIs and the workspace repo are
// read from the machine itself, the rest from context/config.yaml.
// Run from the workspace root:  node reference/scripts/inventory.js
//
// ponytail: hand-rolled YAML reader for the `inventory:` block only (list of flat
// maps, inline or block form). Swap for a real parser if config.yaml ever grows
// nesting there.

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const root = process.cwd();
const esc = require('./lib-workspace.js').esc;

// Working language of the workspace, from config.yaml -> language. Default English.
const lang = (() => {
  try {
    const m = fs.readFileSync(path.join(root, 'context', 'config.yaml'), 'utf8')
      .match(/^language:\s*["']?(\w+)/m);
    return m && m[1].toLowerCase().startsWith('de') ? 'de' : 'en';
  } catch { return 'en'; }
})();

const T = {
  en: {
    skills: 'Skills', connections: 'MCP', tools: 'CLI', repos: 'Repos',
    plugins: 'Plugins', routines: 'Routines', keys: 'API-Keys',
    notConnected: 'not connected', notInstalled: 'not installed', noKey: 'no key stored',
    switchedOff: 'switched off',
    skillsFor: (n) => `${n} skill${n === 1 ? '' : 's'} for it`, noSkill: 'no manual',
    mcp: 'MCP server, registered on this machine',
    pluginFrom: (m, sc) => `Plugin from ${m}, installed for ${sc === 'project' ? 'one project' : 'you'}`,
    projectRepo: 'Repo of a project in this workspace',
    scopeWorkspace: 'in this folder', scopeGlobal: 'everywhere', scopePlugin: 'plugin',
    useIt: 'Use it', removeIt: 'Remove it', copied: 'copied',
    sayUse: (n) => `Run the ${n} skill`, sayRemove: (n) => `Remove the ${n} skill`,
    filter: 'Search skill',
    nSkills: (n) => `${n} skills`,
    fromSources: (n) => `from ${n} sources`, ofTotal: (n) => `of ${n}`,
    inWorkspace: 'in this workspace', scheduled: 'on a schedule',
    xrefKey: 'key stored', xrefCli: 'CLI installed', xrefSkills: (n) => `brings ${n} skills`,
    subMcp: 'of {n} connected', subCli: 'for this workspace', subKeys: 'of {n} stored',
    baseLab: 'System basics, there without setup',
    mcpVia: (x) => `runs via ${x}`, mcpPlugin: (x) => `comes with the ${x} plugin`,
    coveredVia: (c) => `covered by the ${c} CLI`, installedLab: 'installed', subNone: 'none set up yet',
    optional: 'optional',
    setupLab: 'Startup setup', setupSub: (d, t, o) => `${d} of ${t} required steps` + (o ? `, ${o} optional open` : ''),
    stConfig: { t: 'Personalised', done: 'name, domain and language are set', open: 'config.yaml still holds placeholders' },
    stMail: { t: 'Mailbox', done: 'reachable, the briefing can triage', open: 'no route to your mail yet' },
    stCal: { t: 'Calendar', done: 'reachable, appointments show up', open: 'no route to your calendar yet' },
    stFirecrawl: { t: 'firecrawl', done: 'CLI and key are in place', open: 'CLI or key missing, web research stays off' },
    stPlaywright: { t: 'playwright', done: 'installed, a real browser is available', open: 'not installed, no browser control' },
    stBackup: { t: 'Backup repo', done: 'remote set, the evening pushes your state', open: 'no remote, nothing is backed up' },
    stMailStyle: { t: 'Mail style', done: 'derived, drafts sound like you', open: 'not derived yet, drafts use the templates' },
    stDashboard: { t: 'Dashboard runtime', done: 'node is there, this page renders', open: 'node missing, only the chat briefing runs' },
    stStore: { t: 'File storage', done: 'reachable', open: 'documents have to be copied over by hand' },
    stChat: { t: 'Team chat', done: 'reachable', open: 'agreements made in chat stay invisible' },
    stCrm: { t: 'CRM', done: 'reachable', open: 'customer state stays outside' },
    stDev: { t: 'Development', done: 'reachable', open: 'no route to repos or deployments' },
    stPlugins: { t: 'Plugins', done: 'the curated set is installed', open: 'missing: {n}' },
    stRoutine: { t: 'Routine', done: 'runs on a schedule', open: 'nothing runs on its own yet' },
    openConn: 'Connected but not signed in:', openCli: 'Tool not installed:',
    openKey: 'No access key stored:', openNothing: 'Nothing set up here yet:',
    grpWorkspace: 'Your own skills', grpGlobal: 'Skills for every folder',
    grpWorkspaceSub: 'Built for this workspace, they live in .claude/skills',
    grpGlobalSub: 'Available in every project, they live in your home folder',
    grpPluginSub: 'Comes with an installed plugin',
    auditHead: 'Here but not wired into CLAUDE.md',
    audit: {
      dead: 'CLAUDE.md points at something that is not installed here:',
      cli: 'Installed but never mentioned in CLAUDE.md, so it stays unused:',
      key: 'Access key stored but not wired into CLAUDE.md:',
    },
    active: (n, all) => `${n} of ${all} active`, count: (n) => `${n}`,
    workspace: 'This workspace, your evening backup goes here',
    backedUp: (x) => `backed up ${x}`, mayNotRun: 'may no longer run',
    ranToday: 'ran today', ranYesterday: 'last run yesterday', ranDays: (d) => `last run ${d} days ago`,
    hSkills: 'No skill found. Skills live in <code>.claude/skills/</code>; new ones are built with <code>skill-creator</code>',
    hConn: 'No connection entered yet. You connect mail, calendar and file storage once in Claude Cowork under Settings &rarr; Connectors; the instructions are in <code>reference/mcp.md</code>',
    hTools: 'No tool entered yet. firecrawl reads web pages, playwright drives a real browser; the installation is in <code>reference/tools.md</code>',
    hRepos: 'No repo entered yet. Enter name and address in <code>context/config.yaml</code> under <code>inventory.repos</code>',
    hPlugins: 'No plugin entered yet. The package needs none; which ones are worth it is in <code>reference/plugins.md</code>',
    hRoutines: 'No routine entered yet. Routines let Claude work on a schedule, for example the briefing at 7 in the morning; see <code>SETUP.md</code>',
    hKeys: 'No access key entered yet. Some tools need a key of their own, for example firecrawl for reading web pages; how that works is in <code>reference/tools.md</code>',
  },
  de: {
    skills: 'Skills', connections: 'MCP', tools: 'CLI', repos: 'Repos',
    plugins: 'Plugins', routines: 'Routinen', keys: 'API-Keys',
    notConnected: 'nicht verbunden', notInstalled: 'nicht installiert', noKey: 'kein Key hinterlegt',
    switchedOff: 'abgeschaltet',
    skillsFor: (n) => `${n} Skill${n === 1 ? '' : 's'} dafür`, noSkill: 'keine Anleitung',
    mcp: 'MCP-Server, auf dieser Maschine registriert',
    pluginFrom: (m, sc) => `Plugin aus ${m}, installiert fuer ${sc === 'project' ? 'ein Projekt' : 'dich'}`,
    projectRepo: 'Repo eines Projekts in diesem Workspace',
    scopeWorkspace: 'in diesem Ordner', scopeGlobal: 'ueberall', scopePlugin: 'Plugin',
    useIt: 'Benutzen', removeIt: 'Entfernen', copied: 'kopiert',
    sayUse: (n) => `Nutze den Skill ${n}`, sayRemove: (n) => `Entferne den Skill ${n}`,
    filter: 'Skill suchen',
    nSkills: (n) => `${n} Skills`,
    fromSources: (n) => `aus ${n} Quellen`, ofTotal: (n) => `von ${n}`,
    inWorkspace: 'in diesem Workspace', scheduled: 'nach Zeitplan',
    xrefKey: 'Key hinterlegt', xrefCli: 'CLI installiert', xrefSkills: (n) => `bringt ${n} Skills mit`,
    subMcp: 'von {n} verbunden', subCli: 'für diesen Workspace', subKeys: 'von {n} hinterlegt',
    baseLab: 'Systembasis, ohne Einrichtung da',
    mcpVia: (x) => `läuft über ${x}`, mcpPlugin: (x) => `kommt mit dem Plugin ${x}`,
    coveredVia: (c) => `über ${c} CLI abgedeckt`, installedLab: 'installiert', subNone: 'noch keine eingerichtet',
    optional: 'optional',
    setupLab: 'Startup-Setup', setupSub: (d, t, o) => `${d} von ${t} Pflichtschritten` + (o ? `, ${o} optionale offen` : ''),
    stConfig: { t: 'Personalisiert', done: 'Name, Domain und Sprache stehen', open: 'in config.yaml stehen noch Platzhalter' },
    stMail: { t: 'Postfach', done: 'erreichbar, das Briefing kann sortieren', open: 'noch kein Weg zu deiner Mail' },
    stCal: { t: 'Kalender', done: 'erreichbar, Termine tauchen auf', open: 'noch kein Weg zu deinem Kalender' },
    stFirecrawl: { t: 'firecrawl', done: 'CLI und Key sind da', open: 'CLI oder Key fehlt, Web-Recherche bleibt aus' },
    stPlaywright: { t: 'playwright', done: 'installiert, echter Browser verfügbar', open: 'nicht installiert, keine Browser-Steuerung' },
    stBackup: { t: 'Backup-Repo', done: 'Remote gesetzt, der Abend sichert deinen Stand', open: 'kein Remote, nichts wird gesichert' },
    stMailStyle: { t: 'Mail-Stil', done: 'abgeleitet, Entwürfe klingen nach dir', open: 'noch nicht abgeleitet, Entwürfe nutzen die Vorlagen' },
    stDashboard: { t: 'Dashboard-Laufzeit', done: 'node ist da, diese Seite rendert', open: 'node fehlt, es läuft nur das Briefing im Chat' },
    stStore: { t: 'Ablage', done: 'erreichbar', open: 'Dokumente müssen von Hand rüberkopiert werden' },
    stChat: { t: 'Team-Chat', done: 'erreichbar', open: 'Abmachungen aus dem Chat bleiben unsichtbar' },
    stCrm: { t: 'CRM', done: 'erreichbar', open: 'Kundenstand bleibt draußen' },
    stDev: { t: 'Entwicklung', done: 'erreichbar', open: 'kein Weg zu Repos oder Deployments' },
    stPlugins: { t: 'Plugins', done: 'der kuratierte Satz ist installiert', open: 'fehlt: {n}' },
    stRoutine: { t: 'Routine', done: 'läuft nach Zeitplan', open: 'noch läuft nichts von allein' },
    openConn: 'Verbunden, aber nicht angemeldet:', openCli: 'Werkzeug nicht installiert:',
    openKey: 'Kein Zugang hinterlegt:', openNothing: 'Hier ist noch nichts eingerichtet:',
    grpWorkspace: 'Deine eigenen Skills', grpGlobal: 'Skills für jeden Ordner',
    grpWorkspaceSub: 'Für diesen Workspace gebaut, liegen in .claude/skills',
    grpGlobalSub: 'Überall verfügbar, liegen in deinem Benutzerordner',
    grpPluginSub: 'Kommt mit einem installierten Plugin',
    auditHead: 'Da, aber nicht in CLAUDE.md verdrahtet',
    audit: {
      dead: 'CLAUDE.md verweist auf etwas, das hier nicht installiert ist:',
      cli: 'Installiert, aber in CLAUDE.md nirgends erwähnt, bleibt also ungenutzt:',
      key: 'Zugang hinterlegt, aber in CLAUDE.md nicht verdrahtet:',
    },
    active: (n, all) => `${n} von ${all} aktiv`, count: (n) => `${n}`,
    workspace: 'Dieser Workspace, hierhin geht dein Abend-Backup',
    backedUp: (x) => `gesichert ${x}`, mayNotRun: 'läuft womöglich nicht mehr',
    ranToday: 'heute gelaufen', ranYesterday: 'zuletzt gestern', ranDays: (d) => `zuletzt vor ${d} Tagen`,
    hSkills: 'Noch kein Skill gefunden. Skills liegen in <code>.claude/skills/</code>; neue baust du mit <code>skill-creator</code>',
    hConn: 'Noch keine Verbindung eingetragen. Mail, Kalender und Ablage verbindest du einmalig in Claude Cowork unter Einstellungen &rarr; Connectors',
    hTools: 'Noch kein Werkzeug eingetragen. firecrawl liest Webseiten, playwright steuert einen echten Browser',
    hRepos: 'Noch kein Repo eingetragen. Name und Adresse kommen in <code>context/config.yaml</code> unter <code>inventory.repos</code>',
    hPlugins: 'Noch kein Plugin eingetragen.',
    hRoutines: 'Noch keine Routine eingetragen. Routinen lassen Claude nach Zeitplan arbeiten, zum Beispiel das Briefing um 7 Uhr',
    hKeys: 'Noch kein Zugang eingetragen. Manche Werkzeuge brauchen einen eigenen Key, zum Beispiel firecrawl zum Lesen von Webseiten',
  },
}[lang];

// ---------- shared readers ----------
const L = require('./lib-workspace.js')(root);
const { readInventory, skillDirs, skills, plugins, machineRoutines, projectRepos, originUrl, lastCommit,
        firstSentence, installed, mcpServers, hasKey, prettyMcp,
        WORK_CLIS, BASE_CLIS, KNOWN_CLIS } = L;

function routineAge(name) {
  const n = name.toLowerCase();
  const pat = /morning|briefing|daily/.test(n) ? /^briefing-/
    : /week|weekly|review/.test(n) ? /^(weekly|wochenrueckblick)-/
    : /ahead|outlook|vorausblick/.test(n) ? /^(look-?ahead|vorausblick)-/ : null;
  if (!pat) return null;
  let newest = 0;
  for (const dir of [path.join(root, 'inbox'), path.join(root, 'inbox', 'archive')]) {
    let entries = [];
    try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch { continue; }
    for (const e of entries) {
      const p = path.join(dir, e.name);
      if (e.isDirectory()) {
        try { for (const f of fs.readdirSync(p)) if (pat.test(f)) newest = Math.max(newest, fs.statSync(path.join(p, f)).mtimeMs); } catch {}
      } else if (pat.test(e.name)) {
        try { newest = Math.max(newest, fs.statSync(p).mtimeMs); } catch {}
      }
    }
  }
  if (!newest) return null;
  const days = Math.floor((Date.now() - newest) / 86400000);
  return { days, label: days === 0 ? T.ranToday : days === 1 ? T.ranYesterday : T.ranDays(days) };
}

// "plugin:stripe:stripe" and "claude.ai Gmail" are registry names, not reading names.

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
  // Plugin-Namen gehoeren dazu: die Routing-Tabelle nennt sie wie Skills (`| Signal | `ponytail` |`),
  // aber ein Plugin bringt seine Skills unter eigenem Namensraum mit. Ohne diese Zeile meldet
  // der Audit jedes geroutete Plugin als toten Verweis. Gefunden am 23.07.
  const have = new Set([...skills().map((x) => x.name), ...KNOWN_CLIS.filter(installed),
                        ...plugins().filter((p) => p.status).map((p) => p.name)]);
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


const inv = readInventory();
const origin = originUrl();

// config wording wins (it carries the purpose), locally registered servers are added on top
const connectors = inv.connectors.slice();
for (const srv of mcpServers()) {
  const pm = prettyMcp(srv.name);
  const key = (x) => x.toLowerCase().replace(/\W/g, '');
  const known = connectors.find((c) => key(c.name) === key(srv.name) || key(c.name) === key(pm.short));
  if (known) { known.status = srv.status; continue; }
  // machine: registered on this machine but NOT declared in the config — the user's own
  // extras. Their state shows in the detail list, but they are not part of the setup and
  // never enter the "still open" tile.
  connectors.push({ name: pm.short, status: srv.status, fromPlugin: pm.fromPlugin, machine: true,
    purpose: pm.scope ? (pm.fromPlugin ? T.mcpPlugin(pm.scope) : T.mcpVia(pm.scope)) : T.mcp });
}

const repos = inv.repos.slice();
if (origin && !repos.some((r) => (r.url || '').replace(/\.git$/, '') === origin.replace(/\.git$/, ''))) {
  repos.unshift({ name: 'workspace', url: origin, purpose: T.workspace });
}
const backedUp = origin ? lastCommit() : '';

// ---------- rendering ----------
// One pager: seven KPI tiles, closed. Each tile says at a glance how much of that category
// is actually active; clicking it opens the detail list. Nothing scrolls until you ask for it.

// Tooling as a list of expanding rows, not a grid of cards: an opened tile in a grid
// jumped to full width and shoved its neighbours around. As a row it expands in place and
// nothing moves. Layout: icon · count · label · state on the right · chevron.
function kpi(id, icon, num, label, sub, state, body) {
  return `<details class="invrow ${state}" id="kpi-${id}"><summary>`
    + `<span class="invrow-ico"><svg><use href="#${icon}"/></svg></span>`
    + `<span class="invrow-num">${esc(num)}</span>`
    + `<span class="invrow-lab">${esc(label)}</span>`
    + `<span class="invrow-sub">${esc(sub)}</span></summary>`
    + `<div class="invrow-body">${body}</div></details>`;
}

const state = (n, all) => (all === 0 ? 'none' : n === all ? 'ok' : 'part');

// xref = "this also exists over there", NOT a warning — so it must not look amber
const itemRow = (name, purpose, badge, chipText, xref) =>
  `<div class="ivrow"><div class="ivname"><b>${esc(name)}</b>`
  + (badge ? `<span class="inv-badge${xref ? ' xref' : ''}">${esc(badge)}</span>` : '') + `</div>`
  + (purpose ? `<p>${esc(purpose)}</p>` : '')
  + (chipText ? `<code class="inv-chip">${esc(chipText)}</code>` : '') + `</div>`;

const emptyRow = (hint) => `<div class="ivempty">${hint}</div>`;

// the summary already carries the first sentence, the detail only adds what is left
const rest = (s) => (s.full && s.purpose && s.full.startsWith(s.purpose)
  ? s.full.slice(s.purpose.length).trim() : s.full) || '';

// Skills grouped by where they come from. A plugin with 34 skills is ONE line,
// its list opens on click. Flat, 150 entries is not an overview, it is a wall.
function skillGroups(list) {
  const groups = new Map();
  for (const s of list) {
    if (!groups.has(s.scope)) groups.set(s.scope, []);
    groups.get(s.scope).push(s);
  }
  const order = (k) => (k === 'workspace' ? 0 : k === 'global' ? 1 : 2);
  return [...groups.entries()].sort((a, b) => order(a[0]) - order(b[0]) || a[0].localeCompare(b[0]));
}

const groupTitle = (scope) => scope === 'workspace' ? T.grpWorkspace
  : scope === 'global' ? T.grpGlobal : scope.replace(/^plugin:/, '');

const skillPanel = ([scope, items]) =>
  `<details class="ivpanel"><summary><b>${esc(groupTitle(scope))}</b>`
  + `<span class="ivmeta">${esc(T.nSkills(items.length))}</span></summary><div class="ivlist">`
  + items.map((s) =>
      `<div class="sk-row"><div class="sk-head"><b>${esc(s.name)}</b>`
      + `<button class="say-btn" type="button" data-say="${esc(T.sayUse(s.name))}">${esc(T.useIt)}</button>`
      + `<button class="say-btn" type="button" data-say="${esc(T.sayRemove(s.name))}">${esc(T.removeIt)}</button>`
      + `</div><p>${esc(s.purpose || rest(s))}</p></div>`).join('')
  + `</div></details>`;

const skillList = skills();
const groups = skillGroups(skillList);

const cliAll = [...new Set([...inv.clis.map((c) => c.name), ...KNOWN_CLIS])].map((name) => {
  const cfg = inv.clis.find((c) => c.name === name);
  return { name, on: installed(name), purpose: cfg && cfg.purpose, listed: !!cfg,
           base: BASE_CLIS.includes(name) && !cfg };
}).filter((c) => c.on || c.listed).sort((a, b) => a.name.localeCompare(b.name));
const cliList = cliAll.filter((c) => !c.base);
const baseList = cliAll.filter((c) => c.base);

const norm0 = (x) => String(x || '').toLowerCase().replace(/[^a-z0-9]/g, '');
const allRepos = [...repos, ...projectRepos().filter((r) => !repos.some((x) => x.url === r.url))
  .map((r) => ({ ...r, purpose: T.projectRepo }))];
const machinePlugins = plugins();
const pluginList = machinePlugins.length
  ? machinePlugins.map((p) => ({ name: p.name, status: p.status, purpose: T.pluginFrom(p.market, p.scope) }))
  : inv.plugins.map((x) => ({ name: x.name, status: x.status === true, purpose: x.purpose }));
// nur die eingeschalteten zaehlen — ein abgeschaltetes Plugin erfuellt keinen Setup-Schritt
const pluginNames = new Set(machinePlugins.filter((p) => p.status).map((p) => norm0(p.name)));
// Cloud-Routinen (claude.ai) sieht die Maschine nicht, die stehen in der config.
// Lokale Jobs (launchd, crontab, Aufgabenplanung) sieht nur die Maschine. Erst beides
// zusammen ist der ehrliche Stand — vorher meldete die Kachel 0, waehrend drei liefen.
const routineList = [
  ...inv.routines,
  ...machineRoutines().filter((m) => !inv.routines.some((r) => norm0(r.name) === norm0(m.name))),
];
const keyList = inv.accounts.map((a) => ({ ...a, on: hasKey(a.key_env) || a.status === true }));

// Ein CLI ohne Bedienungsanleitung wird geraten statt benutzt: Claude kennt den Befehl,
// aber nicht seine Unterbefehle, und faellt auf --help oder aufs Erfinden zurueck. Die
// Zeile sagt deshalb, wie viele Skills zu diesem Werkzeug gehoeren — firecrawl hat einen,
// gws sieben, und wo null steht, fehlt die Anleitung.
const skillsPerCli = new Map();   // gefuellt weiter unten, sobald norm() existiert
// firecrawl is a CLI, an API key and a family of skills. Technically three things, but for
// the reader it is ONE service — so each entry points at its siblings instead of pretending
// to be an unrelated fourth item.
const norm = (x) => String(x || '').toLowerCase().replace(/[^a-z0-9]/g, '');
const keyNames = new Set(keyList.filter((a) => a.on).map((a) => norm(a.name)));
const cliNames = new Set(cliList.filter((c) => c.on).map((c) => norm(c.name)));

for (const c of cliList) {
  const cn = norm(c.name);
  const n = skillList.filter((s) => {
    const sn = norm(s.name);
    return sn === cn || sn.startsWith(cn);
  }).length;
  if (n) skillsPerCli.set(cn, n);
}
const skillsPerPlugin = new Map(groups
  .filter(([scope]) => scope.startsWith('plugin:'))
  .map(([scope, items]) => [norm(scope.replace(/^plugin:/, '')), items.length]));

// The capability is what counts, not the route: mail via the gws CLI is just as covered
// as mail via the Gmail connector. A disconnected MCP server whose job an installed CLI
// already does is an alternative, not an open setup item.
const CLI_COVERS = [
  { cli: 'gws', re: /gmail|google (calendar|drive|workspace)/i },
  { cli: 'gh', re: /github/i },
  { cli: 'supabase', re: /supabase/i },
  { cli: 'vercel', re: /vercel/i },
];
const coveredBy = (name) => {
  const hit = CLI_COVERS.find((x) => x.re.test(name) && cliNames.has(norm(x.cli)));
  return hit ? hit.cli : '';
};
const mcpOpen = connectors.filter((c) => c.status !== true && !c.fromPlugin && !c.machine && !coveredBy(c.name));

const connOn = connectors.filter((c) => c.status === true).length;
const cliOn = cliList.filter((c) => c.on).length;
const plugOn = pluginList.filter((x) => x.status === true).length;
const keyOn = keyList.filter((a) => a.on).length;

// ---------- the startup setup, as a checklist ----------
// "Part of the setup" means exactly this list and nothing else. It mirrors what /setup
// walks through (SETUP.md, steps 7.1-7.4): the six capability slots, the two tools, the
// backup repo, the mail style, a working dashboard runtime. Everything else on the machine
// is the user's own business and never counts as an open setup item.
//
// A slot is filled by ANY route: a connected MCP server or an installed CLI that does the
// same job. The capability is what counts, never which pipe carries it.
// `machine: true` bleibt draussen. Ein MCP-Server, den jemand privat auf seinem Rechner
// registriert hat, ist NICHT die Verbindung, die das Setup herstellt — sonst haekelt ein
// privater Gmail-Zugang das Postfach des Betriebs gruen ab, waehrend der Selbsttest zwei
// Zeilen tiefer korrekt "noch nicht verbunden" meldet.
const slotFilled = (re, clis) =>
  connectors.some((c) => c.status === true && !c.machine && (re.test(c.name) || re.test(c.purpose || '')))
  || clis.some((x) => cliNames.has(norm(x)));

// "CRM: erreichbar" beantwortet die falsche Frage. Wer hinschaut, will wissen WELCHE
// Verbindung den Platz fuellt — HubSpot oder GoHighLevel ist ein Unterschied, und ohne
// den Namen kann niemand pruefen, ob da das Richtige haengt. Gibt die konkreten Namen
// zurueck, die diesen Schritt erfuellen.
const slotWho = (re, clis) => {
  const names = connectors
    .filter((c) => c.status === true && !c.machine && (re.test(c.name) || re.test(c.purpose || '')))
    .map((c) => c.name);
  for (const x of clis) if (cliNames.has(norm(x))) names.push(x);
  return [...new Set(names)].join(', ');
};

// Kommt die Abdeckung NUR ueber ein installiertes CLI, ist das ein schwaecherer Beleg:
// ein Binary auf der Platte heisst nicht, dass es angemeldet ist. Der Schritt gilt als
// erledigt, sagt aber dazu, worauf er sich stuetzt.
const cliOnly = (re, clis) =>
  clis.some((x) => cliNames.has(norm(x)))
  && !connectors.some((c) => c.status === true && !c.machine && (re.test(c.name) || re.test(c.purpose || '')));

const fileHere = (rel) => { try { return fs.existsSync(path.join(root, rel)); } catch { return false; } };
const configClean = () => {
  try {
    const raw = fs.readFileSync(path.join(root, 'context', 'config.yaml'), 'utf8');
    return !/\[(YOUR NAME|DEIN NAME|your-company|deine-firma)[^\]]*\]/i.test(raw);
  } catch { return false; }
};

// Der kuratierte Satz. Er wird in Schritt 7.1 mitinstalliert, wie die CLIs — das ist der
// Kern des Angebots: taeglich erscheinen neue Plugins, und die Auswahl zu treffen ist die
// Arbeit, die dem Nutzer abgenommen wird. Wer sie hinterher selbst installieren muesste,
// haette genau diese Arbeit wieder.
// EINE Ausnahme in der Behandlung, nicht in der Auswahl: claude-mem bringt einen Daemon
// (ein dauerhaft im Hintergrund laufendes Programm) und eine eigene Datenbank mit und
// protokolliert gelesene Projektinhalte. Es wird mitinstalliert, aber der Setup-Schritt
// sagt in einem Satz was es tut, damit ein Nein moeglich ist, solange es noch etwas
// aendert. Details: reference/plugins.md.
const SETUP_PLUGINS = ['skill-creator', 'ponytail', 'claude-code-setup', 'code-review',
                       'claude-md-management', 'impeccable', 'superpowers', 'claude-mem'];
const missingPlugins = SETUP_PLUGINS.filter((n) => !pluginNames.has(norm0(n)));

const SETUP_STEPS = [
  { req: true,  ok: configClean(),                                        lab: T.stConfig },
  { req: true,  ok: slotFilled(/mail|gmail|outlook|365/i, ['gws']),       lab: T.stMail,
    who: slotWho(/mail|gmail|outlook|365/i, ['gws']),
    via: cliOnly(/mail|gmail|outlook|365/i, ['gws']) ? 'gws' : null },
  { req: true,  ok: slotFilled(/calendar|kalender|365/i, ['gws']),        lab: T.stCal,
    who: slotWho(/calendar|kalender|365/i, ['gws']),
    via: cliOnly(/calendar|kalender|365/i, ['gws']) ? 'gws' : null },
  { req: true,  ok: cliNames.has(norm('firecrawl')) && keyNames.has(norm('firecrawl')), lab: T.stFirecrawl },
  { req: true,  ok: cliNames.has(norm('playwright')),                     lab: T.stPlaywright },
  { req: true,  ok: !!origin,                                             lab: T.stBackup },
  { req: true,  ok: fileHere('context/EMAIL_STYLE.md'),                   lab: T.stMailStyle },
  { req: true,  ok: installed('node'),                                    lab: T.stDashboard },
  { req: true,  ok: missingPlugins.length === 0,                          lab: T.stPlugins,
    note: missingPlugins.join(', ') },
  { req: false, ok: slotFilled(/drive|sharepoint|storage|ablage/i, ['gws']), lab: T.stStore,
    who: slotWho(/drive|sharepoint|storage|ablage/i, ['gws']) },
  { req: false, ok: slotFilled(/slack|teams|chat/i, []),                  lab: T.stChat,
    who: slotWho(/slack|teams|chat/i, []) },
  { req: false, ok: slotFilled(/hubspot|salesforce|crm|pipedrive|gohighlevel|ghl/i, []), lab: T.stCrm,
    who: slotWho(/hubspot|salesforce|crm|pipedrive|gohighlevel|ghl/i, []) },
  { req: false, ok: slotFilled(/github|supabase|vercel/i, ['gh', 'supabase', 'vercel']), lab: T.stDev,
    who: slotWho(/github|supabase|vercel/i, ['gh', 'supabase', 'vercel']) },
  { req: false, ok: routineList.length > 0,                               lab: T.stRoutine },
];

const reqSteps = SETUP_STEPS.filter((x) => x.req);
const reqDone = reqSteps.filter((x) => x.ok).length;
const optOpen = SETUP_STEPS.filter((x) => !x.req && !x.ok).length;
const pct = Math.round((reqDone / reqSteps.length) * 100);

const stepRow = (x) => `<div class="ivrow ivstep${x.ok ? ' done' : ''}">`
  + `<div class="ivname"><span class="ivtick" aria-hidden="true">${x.ok ? '✓' : '○'}</span>`
  + `<b>${esc(x.lab.t)}</b>`
  + (x.req ? '' : `<span class="inv-badge xref">${esc(T.optional)}</span>`) + `</div>`
  + `<p>${x.ok && x.who ? '<b>' + esc(x.who) + '</b> — ' : ''}`
  + `${esc((x.ok ? x.lab.done : x.lab.open).replace('{n}', x.note || ''))}${x.ok && x.via ? ' (' + T.coveredVia(x.via) + ')' : ''}</p></div>`;

const setupTile = `<details class="kpi ${pct === 100 ? 'ok' : 'part'} wide" id="kpi-setup"><summary>`
  + `<span class="kpi-ico"><svg><use href="#i-open"/></svg></span>`
  + `<span class="kpi-num">${pct}%</span>`
  + `<span class="kpi-lab">${esc(T.setupLab)}</span>`
  + `<span class="kpi-sub">${esc(T.setupSub(reqDone, reqSteps.length, optOpen))}</span>`
  + `<span class="kpi-bar" aria-hidden="true"><i style="width:${pct}%"></i></span></summary>`
  + `<div class="kpi-body">${SETUP_STEPS.map(stepRow).join('')}</div></details>`;

// Findings from the CLAUDE.md cross-check are NOT setup steps, they are a health note.
// They sit under the grid, quiet, so the setup number stays honest.
const findings = audit();
const auditNote = findings.length
  ? `<div class="inv-note"><b>${esc(T.auditHead)}</b>`
    + findings.map((x) => `<p>${esc(T.audit[x.kind])} ${esc(x.items.join(', '))}</p>`).join('')
    + `</div>` : '';

const out = [
  `<div id="inv-i18n" data-filter="${esc(T.filter)}" data-copied="${esc(T.copied)}" hidden></div>`,
  `<div class="kpigrid">`,
  setupTile,
  `</div>`,
  `<div class="invlist">`,

  kpi('skills', 'i-cmd', skillList.length, T.skills, T.fromSources(groups.length),
    skillList.length ? 'ok' : 'none',
    groups.length ? groups.map(skillPanel).join('') : emptyRow(T.hSkills)),

  kpi('conn', 'i-plug', connOn, T.connections, T.subMcp.replace('{n}', connectors.length),
    connectors.length ? (mcpOpen.length ? 'part' : 'ok') : 'none',
    connectors.length
      ? connectors.map((c) => {
          const cov = c.status !== true && coveredBy(c.name);
          return itemRow(c.name, c.purpose,
            c.status === true ? '' : (cov ? T.coveredVia(cov) : T.notConnected),
            '', !!cov || (c.status !== true && (c.fromPlugin || c.machine)));
        }).join('')
      : emptyRow(T.hConn)),

  kpi('cli', 'i-cli', cliList.filter((c) => c.on).length, T.tools, T.subCli,
    state(cliOn, cliList.length),
    cliList.length
      ? cliList.map((c) => {
          if (!c.on) return itemRow(c.name, c.purpose, T.notInstalled, '', false);
          const bits = [];
          if (keyNames.has(norm(c.name))) bits.push(T.xrefKey);
          bits.push(skillsPerCli.has(norm(c.name))
            ? T.skillsFor(skillsPerCli.get(norm(c.name))) : T.noSkill);
          return itemRow(c.name, c.purpose, bits.join(' · '), '', true);
        }).join('')
        + (baseList.length
            ? `<div class="ivrow ivbase"><div class="ivname">${esc(T.baseLab)}</div>`
              + `<p>${esc(baseList.map((c) => c.name).join(', '))}</p></div>` : '')
      : emptyRow(T.hTools)),

  kpi('repos', 'i-repo', allRepos.length, T.repos, T.inWorkspace,
    allRepos.length ? 'ok' : 'none',
    allRepos.length
      ? allRepos.map((r, i) => itemRow(r.name, r.purpose,
          i === 0 && backedUp ? T.backedUp(backedUp) : '', r.url)).join('')
      : emptyRow(T.hRepos)),

  // Die Zahl ist der EINGESCHALTETE Stand, nicht der installierte. Ein abgeschaltetes
  // Plugin ist weiter gelistet und tut nichts; "14 installiert" waere deshalb eine Zahl,
  // die beruhigt statt zu informieren. Gefunden am 23.07.: 14 gemeldet, 9 liefen.
  kpi('plugins', 'i-puzzle', plugOn, T.plugins, T.active(plugOn, pluginList.length),
    state(plugOn, pluginList.length),
    pluginList.length
      // Der Aus-Zustand schlaegt jeden anderen Hinweis. Vorher gewann das
      // Skill-Abzeichen, wenn ein Plugin Skills mitbringt — ausgerechnet bei den
      // groessten Plugins blieb "abgeschaltet" damit unsichtbar. 23.07.
      ? pluginList.map((x) => itemRow(x.name, x.purpose,
          x.status !== true ? T.switchedOff
            : (skillsPerPlugin.has(norm(x.name)) ? T.xrefSkills(skillsPerPlugin.get(norm(x.name))) : ''),
          '', x.status === true && skillsPerPlugin.has(norm(x.name)))).join('')
      : emptyRow(T.hPlugins)),

  kpi('routines', 'i-clock', routineList.length, T.routines, routineList.length ? T.scheduled : T.subNone,
    routineList.length ? 'ok' : 'none',
    routineList.length
      ? routineList.map((r) => {
          const age = routineAge(r.name);
          return itemRow(r.name, r.purpose, age ? (age.days > 2 ? T.mayNotRun : age.label) : '', r.schedule);
        }).join('')
      : emptyRow(T.hRoutines)),

  kpi('keys', 'i-key', keyOn, T.keys, T.subKeys.replace('{n}', keyList.length),
    state(keyOn, keyList.length),
    keyList.length
      ? keyList.map((a) => itemRow(a.name, a.purpose,
          a.on ? (cliNames.has(norm(a.name)) ? T.xrefCli : '') : T.noKey,
          '', a.on)).join('')
      : emptyRow(T.hKeys)),

  `</div>`,
  auditNote,
].join('');

// What is installed but not wired into CLAUDE.md ends up right under the overview —
// this is exactly the case where Claude forgets in everyday work that the thing exists.
const outAll = out;

process.stdout.write(outAll);

// --- self-check:  node reference/scripts/inventory.js --selftest
if (process.argv.includes('--selftest')) {
  const assert = require('assert');
  const cards = outAll.match(/sk-row/g) || [];
  const tiles = (outAll.match(/class="kpi /g) || []).length;
  assert.ok(tiles === 7 || tiles === 8, `expected 7 tiles (8 with the open one), got ${tiles}`);
  assert.ok(/kpi-lab">Skills</.test(outAll), 'skills tile missing');
  assert.ok(outAll.split('<details').length > 8, 'no detail panels rendered');
  assert.ok(!/—/.test(outAll), 'em-dash leaked into the fragment');
  assert.ok(!/undefined|\[object/.test(outAll), 'placeholder value leaked into the fragment');
  console.error(`ok, 7 tiles, ${cards.length} skills listed`);
}
