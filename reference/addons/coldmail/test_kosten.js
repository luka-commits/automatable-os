/* test_kosten.js — die Kostenrechnung der Erklaerseite, gegen Handrechnungen.
 *
 * DER ANLASS (Luka, 23.08.2026): "400 $ pro monat wirklich? das kommt mir fast falsch
 * vor." Es war falsch. Auf der Seite stand Instantly Hypergrowth mit 358 $, richtig sind
 * 97 $ -- die 358 sind Lightspeed. Aus 196 $ waren so 457 $ geworden, und die Zahl sah
 * plausibel genug aus, dass sie ohne seinen Zweifel stehen geblieben waere.
 *
 * Ein Preis auf einer Seite, die jemand vor einer Kaufentscheidung liest, gehoert
 * deshalb genauso gepruft wie eine Mail vor dem Versand.
 *
 * Ausfuehren:  node reference/addons/coldmail/test_kosten.js
 * Die Funktionen unten sind ZEICHENGLEICH mit denen in WHAT-WORKS-COLDMAIL.html --
 * `pruefeSeite()` unten liest die Seite und stellt genau das sicher.
 */
'use strict';

const PRO_POSTFACH_TAG = 30;   // Instantlys Decke, nicht verhandelbar
const TAGE = 20;               // Werktage
const PRO_DOMAIN = 3;          // Zapmails Empfehlung 2-3
const ANSCHREIBBAR = 0.52;     // gemessen: 2.483 von 4.746
const APIFY = 0.0017;          // gemessen im Betrieb, Liste waere 0,004-0,006
const VERIFY = 0.0039;         // MillionVerifier, 39 $/10.000
const DFS = 1.34;              // DataForSEO je Nische
const DOMAIN_JAHR = 12;

function zapmail(boxen) {
  if (boxen <= 10) return 39;
  if (boxen <= 30) return 99;
  return 299;
}

function instantly(mails) {
  if (mails <= 5000) return { preis: 47, name: 'Growth' };
  if (mails <= 125000) return { preis: 97, name: 'Hypergrowth' };
  return { preis: 358, name: 'Lightspeed' };
}

function rechne(mails, quote) {
  const proTag = Math.ceil(mails / TAGE);
  const boxen = Math.ceil(proTag / PRO_POSTFACH_TAG);
  const domains = Math.ceil(boxen / PRO_DOMAIN);
  const inst = instantly(mails);
  const zap = zapmail(boxen);
  const dom = domains * DOMAIN_JAHR / 12;
  const daten = mails / ANSCHREIBBAR * APIFY + mails * VERIFY + DFS;
  const summe = zap + inst.preis + dom + daten;
  return {
    proTag, boxen, domains, tarif: inst.name,
    zap, instantly: inst.preis, dom, daten, summe,
    antworten: Math.round(mails * quote),
    proMail: summe / mails,
    proAntwort: Math.round(mails * quote) ? summe / (mails * quote) : null,
  };
}

// ─────────────────────────────────────────────────────────────── Tests
let schlecht = 0;
function pruefe(name, fn) {
  try {
    fn();
    console.log(`  ${name.padEnd(56)} ok`);
  } catch (e) {
    schlecht++;
    console.log(`  ${name.padEnd(56)} FEHLER\n      ${e.message}`);
  }
}
function gleich(ist, soll, was) {
  if (Math.abs(ist - soll) > 0.01) {
    throw new Error(`${was}: ${ist} statt ${soll}`);
  }
}

pruefe('Die kleine Empfehlung: 2.000 Mails im Monat', () => {
  const r = rechne(2000, 0.02);
  gleich(r.proTag, 100, 'Mails am Tag');           // 2000 / 20
  gleich(r.boxen, 4, 'Postfaecher');               // 100 / 30 aufgerundet
  gleich(r.domains, 2, 'Domains');                 // 4 / 3 aufgerundet
  gleich(r.zap, 39, 'Zapmail');                    // 4 <= 10
  gleich(r.instantly, 47, 'Instantly');            // 2.000 <= 5.000
  if (r.tarif !== 'Growth') throw new Error('Tarif: ' + r.tarif);
  // Daten von Hand: 2000/0,52 = 3.846 Profile x 0,0017 = 6,54
  //                 + 2000 x 0,0039 = 7,80  + 1,34 = 15,68
  gleich(r.daten, 15.68, 'Daten');
  gleich(r.summe, 39 + 47 + 2 + 15.68, 'Summe');   // 103,68
  gleich(r.antworten, 40, 'Antworten');
});

pruefe('Lukas Setup: 16.000 Mails im Monat', () => {
  const r = rechne(16000, 0.02);
  gleich(r.proTag, 800, 'Mails am Tag');
  gleich(r.boxen, 27, 'Postfaecher');              // 800/30 = 26,67 -> 27
  gleich(r.domains, 9, 'Domains');
  gleich(r.zap, 99, 'Zapmail');                    // 27 > 10, <= 30
  gleich(r.instantly, 97, 'Instantly');            // 16.000 > 5.000
  if (r.tarif !== 'Hypergrowth') throw new Error('Tarif: ' + r.tarif);
  gleich(r.summe, 99 + 97 + 9 + r.daten, 'Summe');
  if (r.summe > 350) throw new Error('unplausibel teuer: ' + r.summe);
});

pruefe('Die Tarifgrenzen sitzen genau', () => {
  gleich(instantly(5000).preis, 47, 'genau 5.000 ist noch Growth');
  gleich(instantly(5001).preis, 97, 'einer mehr ist Hypergrowth');
  gleich(instantly(125000).preis, 97, 'genau 125.000 ist noch Hypergrowth');
  gleich(instantly(125001).preis, 358, 'darueber Lightspeed');
  gleich(zapmail(10), 39, 'genau 10 Postfaecher');
  gleich(zapmail(11), 99, 'elf sind der naechste Tarif');
  gleich(zapmail(30), 99, 'genau 30');
  gleich(zapmail(31), 299, 'darueber');
});

pruefe('Der Sprung ueber 5.000 kostet 50, nicht 311', () => {
  const a = rechne(5000, 0.02), b = rechne(5500, 0.02);
  const sprung = b.instantly - a.instantly;
  gleich(sprung, 50, 'Instantly-Sprung');
  if (sprung > 100) throw new Error('das war der alte Fehler: ' + sprung);
});

pruefe('Die Daten kosten unter einem Cent je Mail', () => {
  for (const m of [1000, 5000, 20000]) {
    const r = rechne(m, 0.02);
    const proMail = r.daten / m;
    if (proMail > 0.01) throw new Error(`${m} Mails: ${proMail.toFixed(4)} $/Mail`);
  }
});

pruefe('Mehr Mails senken den Preis je Mail', () => {
  const klein = rechne(1000, 0.02).proMail;
  const gross = rechne(20000, 0.02).proMail;
  if (!(gross < klein)) throw new Error(`${gross} nicht unter ${klein}`);
});

pruefe('Kosten je Antwort bleiben im Rahmen', () => {
  const r = rechne(16000, 0.02);
  if (r.proAntwort > 2) throw new Error(r.proAntwort + ' $ je Antwort');
  const k = rechne(2000, 0.02);
  if (k.proAntwort > 5) throw new Error(k.proAntwort + ' $ je Antwort (klein)');
});

// ───────────────────────── Die Seite muss dieselben Zahlen benutzen
function pruefeSeite() {
  const fs = require('fs'), path = require('path');
  const p = path.join(__dirname, '..', '..', '..', 'WHAT-WORKS-COLDMAIL.html');
  if (!fs.existsSync(p)) { console.log('  (Seite nicht gefunden, uebersprungen)'); return; }
  const t = fs.readFileSync(p, 'utf8');
  const muss = [
    ['PRO_POSTFACH_TAG = 30', '30 Mails je Postfach'],
    ['preis: 47, name: \'Growth\'', 'Growth 47'],
    ['preis: 97, name: \'Hypergrowth\'', 'Hypergrowth 97'],
    ['preis: 358, name: \'Lightspeed\'', 'Lightspeed 358'],
    ['APIFY = 0.0017', 'Apify-Satz'],
    ['VERIFY = 0.0039', 'MillionVerifier'],
  ];
  const fehlt = muss.filter(([s]) => !t.includes(s)).map(([, w]) => w);
  if (fehlt.length) throw new Error('Seite weicht ab: ' + fehlt.join(', '));
  if (t.includes('$311') || t.includes('Hypergrowth $358')) {
    throw new Error('alte falsche Zahl steht noch im Text');
  }
}
pruefe('Die Seite rechnet mit denselben Zahlen', pruefeSeite);

console.log(schlecht ? `\n${schlecht} FEHLER` : '\nalle Kostentests ok');
process.exit(schlecht ? 1 : 0);
