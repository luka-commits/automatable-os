# `markt` — the reference copy (A/B)

> **This file is the source of truth for the markt body.** Not the Instantly template. The first time
> this decision was made, the copy lived only in Instantly, was never written there either, and was lost
> (journal, 2026-07-25). Edit here, then push to Instantly, never the other way round.

> ## ⚠️ Stand 22.08.2026 — der Prosa-Teil unten ist ueberholt, die Schreibkarte nicht
>
> **Aktuell und gueltig ist der Codeblock § Die Schreibkarte** (146 Zeilen, neu geschrieben am
> 22.08.). Nur den liest `write_mail.py`, und nur der beschreibt die Mail, wie sie heute
> aussieht: Anrede · ein Satz mit den gemessenen Nachbarn und dem Ort · eine Bruecke ·
> drei bis fuenf Stichpunkte · ein fester Abschluss. **Der Schreiber liefert davon einzig die
> Stichpunkte.**
>
> **Alles zwischen hier und der Karte beschreibt die Sechs-Block-Fassung vom 27.07.** --
> Grund-Satz mit Kohortenzahl, ein Block "wo er vorn liegt", Scores, "71 checks", der
> Positions-Satz, die Urteilszeile. Davon gilt nichts mehr. Es steht noch da, weil die
> Herleitung (warum welcher Block wo stand, welche Formulierung woran gescheitert ist) beim
> naechsten Umbau Gold wert ist und ein eigener Durchgang wird. **Wer die Copy aendern will,
> aendert die Karte.** Was heute wirklich in der Mail steht, steht in
> [`instantly_markt.html`](instantly_markt.html) -- 15 Zeilen, in zehn Sekunden gelesen.

Locked with Luka on 2026-07-25. Two variants, one variable: **prose vs bullets.** Everything else is
byte-identical, otherwise the test measures nothing.

## Der Rahmen — was diese Mail tut, in welcher Reihenfolge, und wer welchen Teil schreibt

> Festgelegt am 27.07.2026, nachdem eine ganze Session lang an Formulierungen geschraubt
> wurde, ohne dass der Rahmen feststand. Wer hier etwas aendern will, aendert es HIER
> zuerst, nicht im Prompt.

**Das Ziel der Mail:** eine Antwort. Nicht ein Verkauf, nicht ein Termin, nicht Bildung.
Alles, was nicht auf eine Antwort einzahlt, kommt raus.

**Der Weg dahin, in einem Satz:** wir zeigen ihm eine Sache ueber seinen Markt, die er
selbst nicht sehen kann, und lassen erkennbar mehr davon durchblicken.

**Der Ablauf. Sechs Bloecke, feste Reihenfolge, kein Block ist optional:**

| # | Block | Was er leistet | Wer schreibt |
|---|---|---|---|
| 1 | Betreff | die Marktaussage, kein Pitch: `bedford locksmiths, you and gold` | Python |
| 2 | Anrede | `hey gold,` — casualisiert, klein | Python |
| 3 | Grund | `i just looked at {namen} and the other {n} locksmiths in {gebiet}, and how they compare to {firma}. here are some insights you might find interesting.` Beantwortet „warum schreibt der mir" in der ersten Zeile und kündigt an, was kommt. Seit 27.07. ohne „reaching out because" und ohne das Etikett „your two closest competitors" — die Namen stehen für sich, es sind seine Nachbarn | Python |

**`{n}` und `{gebiet}` müssen zusammenpassen — sonst ist der erste Satz widerlegbar (27.07.).**
Der Satz stand als „the other 10 locksmiths in birmingham". Die 10 sind aber die *zehn
nächsten Nachbarn*, die Vergleichskohorte. In Birmingham gibt es Hunderte, in London
Tausende — der Empfänger braucht zwei Sekunden, um den ersten Satz der Mail zu widerlegen.
Die Zahl war richtig, ihr Etikett falsch.

Deshalb eine Kaskade, jede Stufe mit einer Zahl, die wir wirklich gezählt haben:

| Bedingung | `{n}` / `{gebiet}` | Beispiel |
|---|---|---|
| Region hat **≥ 15** Betriebe | die Region und ihre Zahl | `the other 184 locksmiths in west midlands` |
| Region ist kleiner | das Land und der Gesamtscrape | `the other 4,745 locksmiths across the uk` |

**15**, weil darunter die Aussage dünn wird („the other 5 locksmiths in rutland" klingt nach
Dorf, nicht nach Markt). Gemessen: 95 % der Leads bekommen ihre Region, 5 % das Land.
**Niemals „alle"** — wir kennen 4.746 gescrapte Betriebe, nicht die Grundgesamtheit.

**Die Zahl zählt den ganzen Scrape, auch die aussortierten Ketten** (Greater London 946,
nicht 772). Der Satz sagt „ich habe mir X angesehen", und das stimmt — eine Timpson-Filiale
ist ein Schlüsseldienst im selben Markt, wir schreiben sie nur nicht an. Damit stehen im
selben Text zwei Grundgesamtheiten: die Recherche-Menge oben, die Wettbewerbs-Kohorte unten
(„4 of the 11 nearest you"). Beide sind wahr und beantworten verschiedene Fragen — wer das
je vereinheitlichen will, entscheidet sich HIER, nicht in einem der beiden Skripte.
Die Zehn-Nachbarn-Kohorte bleibt, wo sie hingehört: in den Stichpunkten, wo sie als
„where 4 of the 11 nearest you do" beschriftet ist und nicht als Stadt.
| 3b | — | Der nächste Absatz fängt **direkt mit der Erkenntnis** an. Kein „overall", kein „so", kein „first off": die Einleitung hat sie gerade angekündigt, und ein Räuspern danach kostet die eine Zeile, die der Leser sicher liest | Regel |
| 4 | **Wo er vorn liegt** | EIN Vergleich, den er selbst nicht ziehen kann. Senkt die Abwehr und beweist in einem Satz, dass wir gerechnet haben | **Modell** |
| 5 | **Was ich aendern wuerde** | zwei bis drei Punkte, je Befund und Kosten im selben Atemzug. Kein Loesungsweg | **Modell** |
| 6 | Identitaet, Zahlen, Angebot | wer schreibt (spaet, nach dem Wert), die zwei Scores, der Kontrast zu 73 Checks, die Bitte | Python |

**Warum Block 4 vor Block 5 steht:** eine Mangelliste von einem Fremden wird nicht gelesen.
Ein Vergleich, den er nicht kennt, schon — und danach ist er bereit, den Rest zu hoeren.

**Warum Block 6 hinten steht:** wer sich frueh vorstellt, verkauft. Wer erst liefert, hat
geliefert. Die Frage „wer schickt mir das" kommt beim Leser genau dort, wo wir sie
beantworten.

**Was FEST ist und nie vom Modell kommt:** Betreff, Anrede, der Grund, die Identitaet, die
Scores, das Angebot, die Verabschiedung. Das sind bei 3.593 Mails 3.593 Mal derselbe Satz
mit anderen Zahlen — ein Modell wuerde ihn 3.593 Mal minimal anders formulieren, ohne dass
einer dieser Unterschiede jemandem nuetzt.

**Was das Modell schreibt:** nur die Bloecke 4 und 5. Es bekommt fertige, geprueffte Fakten
(`brief.py`) und ordnet sie. Es darf keine Zahl, keinen Vergleich und keine Ursache
hinzufuegen, und `verify_mail.py` setzt das mechanisch durch.

**Was die zwei Varianten unterscheidet, und sonst NICHTS:** Block 4 und 5 als Fliesstext
gegen Block 4 als Satz plus Block 5 als Liste. Gleiche Fakten, gleiche Reihenfolge, gleiches
Urteil. Jede Abweichung darueber hinaus macht den Test wertlos, weil dann zwei Dinge
gleichzeitig gemessen werden.

**Keine Ueberschriften, in keiner Variante.** Nicht „what's working well:", nicht „what i
would fix:". Das ist Report-Sprache in einer Nachricht von Mensch zu Mensch. Die Liste in
Variante B bekommt einen gesprochenen Einstieg („three things i'd fix, in order:"), keine
Marke.

---

## Wie es heute aussieht, beide Varianten

> Ersetzt die frueheren Abschnitte "The shape", "Variant A" und "Variant B". Die zeigten
> noch Ueberschriften im Text und einen eigenen Verdict-Block; beides gibt es nicht mehr.
> Ein Spec, der dem Code widerspricht, ist schlimmer als keiner.

**Variante A, Fliesstext** (Mobile Locksmith Domestic and Auto, Bedford):

> hey mobile locksmith domestic,
>
> reaching out because i looked at your closest competitor, gold, plus the other 8
> locksmiths in bedford, and how they all compare to mobile locksmith domestic.
>
> 135 reviews puts you second in bedford out of 11 locksmiths, and into the top quarter of
> locksmiths uk wide, and the 43 photos on your profile beat the typical uk locksmith's 14
> by a long way. the work and the reputation are clearly there.
>
> the profile is what's letting that down though. there's no opening hours set, so someone
> locked out at 2am can't tell if you'll pick up, and your reviews keep mentioning new car
> key and car key replacement while your profile lists neither, so those searches are going
> straight to someone else. the site's in good shape, but there's no map on the page, so
> anyone checking if you cover their street has to go dig that up themselves.
>
> in case you're wondering, i'm a freelancer doing local marketing. your google profile came
> out at 5 of 7, and your site at 10 of 12, on the things anyone can check from outside. the
> full report goes through 71 checks across four areas, your google profile, your website,
> your search visibility and how ai assistants answer when someone asks for a locksmith near
> you, and it shows what moves each number. happy to send it over, just say the word.
>
> luka

**Variante B, Stichpunkte** (Carlo's Locksmith Bedford). Bloecke 1 bis 3 und 6 sind
identisch, nur 4 und 5 aendern die Form:

> your website is in great shape, 43 photos on the profile against a bedford middle of the
> pack at 14, and it's one of the few sites round here actually built to be found.
>
> three things pulling you down though:
>
> no 24 hours shown, where 4 other locksmiths in bedford have it, so the 2am call goes
> straight to one of them
>
> profile set to locksmith only, while the most-reviewed firms in town are also listed as
> emergency locksmith service, so those searches never even reach you
>
> 8 reviews against a uk median of 19, and you're 10th of 11 locksmiths in bedford by review
> count, so it's not your rating holding you back, it's the number

**Die Vorlage liegt als [`instantly_markt.html`](instantly_markt.html) im Repo**, nicht nur in
Instantly — dieselbe Entscheidung wie bei der Copy am 25.07.: was nur im Werkzeug lebt, ist beim
nächsten Mal nicht auffindbar. Zusammengesetzt ansehen, bevor sie hochgeht:
`python3 preview_mail.py --run runs/locksmith-bedford`. Der Prüfer dort ist ein anderer als
`verify_mail.py`: er prüft den **Zusammenbau** (fehlende Spalte, nicht ersetzter Platzhalter,
Zeile ins Leere), nicht die Aussagen.

**Der Betreff** ist in beiden Varianten `{area} {niche}s, you and {competitor_1}` — eine
Marktaussage, kein Pitch. Er kommt fertig als Spalte `subject` aus `export_cohort.py`, in
Instantly steht nur `{{subject}}`.

Vorher stand dort `{area} {niche}s, all {market_count}`, und das war **je Region derselbe
Betreff**: gemessen am 28.07. über alle 61 exportierten Regionen 62 verschiedene Betreffzeilen
für 4.273 Mails, in Greater London 844 mal dieselbe. Mit dem nächsten Nachbarn sind es 2.612,
schlimmster Fall 31. Der Name ist derselbe, den der Einstiegssatz ohnehin nennt — der Betreff
verrät also nichts, was die erste Zeile nicht sofort einlöst. Ohne Nachbarn (Kettenfilter,
einziger Betrieb der Region) fällt er auf die Zählung zurück.

**Warum die Identitaet hinten steht.** Wer sich frueh vorstellt, verkauft. Wer erst
liefert, hat geliefert. Die Frage „wer schickt mir das" kommt beim Leser genau dort, wo wir
sie beantworten.

## Die Schreibkarte — das EINZIGE, was der Agent liest

> Der Regelblock oben ist die Herleitung: 245 Zeilen mit Messwerten, Zitaten und der
> Geschichte jeder Regel. Das ist für **Menschen**, die verstehen wollen, warum etwas so
> ist. Der Agent braucht die Archäologie nicht, und sie kostet ihn Zeit.
>
> Von den ~24 Regeln oben erzwingt `pool.py` inzwischen **zwölf** — welche Befunde
> genommen werden, wie viele, in welcher Satzform, mit welchen Blickwinkeln, ob die
> Antwortquote Lob oder Mangel ist, ob der Automatisierungshinweis kommt. Das sind
> Auswahlregeln, keine Schreibregeln. Vier weitere betreffen die Website, die wir nicht
> mehr messen.
>
> Übrig bleibt, was wirklich das Formulieren betrifft. `write_mail._regeln()` lädt weiter
> den vollen Block; die Karte hier lädt `pool`-basierte Agenten-Prompts.

```
SCHREIBKARTE — du formulierst, du entscheidest nicht.

DU LIEFERST GENAU EINS: die Stichpunkte, `tip_1` bis `tip_5`.
Anrede, Satz 1 (die gemessenen Nachbarn plus der Ort), die Bruecke darueber und der
Abschluss stehen fest in der Vorlage oder kommen fertig aus `export_cohort.py`. Keinen
Positions-Satz, keine Urteilszeile, keine Anrede, keine Signatur. Wenn du etwas davon
schreibst, wird es weggeworfen.

DIE ZEILEN KOMMEN AUS `zeilen` IM DATENBLATT, du GLAETTEST sie nur.
Keine hinzufuegen, keine weglassen, keine Zahl aendern. Umstellen und Woerter tauschen ist
erlaubt, Inhalt aendern nicht.

═══════════════════════════════════════════════════════════════════════════════
ZWEI GRENZEN, DIE `verify_mail.py` MECHANISCH PRUEFT. Reissen sie, faellt die Mail
durch und der Lead kommt zurueck auf den Stapel.
  1  Jeder Stichpunkt hoechstens 80 ZEICHEN.
  2  Hoechstens EIN Nachsatz je Zeile (ein " so ", nicht zwei).
Beides gilt seit dem 30.07. und wurde bis zum 22.08. nie eingehalten: von 66
geschriebenen Stichpunkten rissen 65 die 80 Zeichen, Median 116, laengster 150.
═══════════════════════════════════════════════════════════════════════════════

DIE ZEILEN-FORMEL: STATUS QUO, HANDLUNG, WARUM -- alle drei in EINEM Satz.
`fact_sheet.formel()` prueft auch das mechanisch.

  "there's nothing under services, put five in so google matches you to the job"
   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^  ^^^^^^^^^^^  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   was IST                         was TUN      was es BRINGT

Der Status quo ist nicht Deko, er ist der Beweis, dass wirklich jemand nachgesehen hat.
Eine Zeile ohne Zahl oder Zustand koennte an jeden gehen.

80 ZEICHEN UND DREITEILIG GEHT ZUSAMMEN, es ist nachgemessen. Der Grund wird dabei auf
drei bis fuenf Woerter eingekocht, nicht weggelassen:
  76  "there's nothing under services, put five in so google matches you to the job"
  74  "you're on 1 photo where most have 14, add a dozen so people ring you first"
  76  "2 of google's 10 categories are set, fill the rest so more searches find you"
  66  "you're not posting, start and the profile looks as busy as you are"

DER NUTZEN-TEIL IST DER STAERKSTE, WENN ER BENENNT, WER DEN AUFTRAG SONST BEKOMMT.
Das ist die schaerfste Form, die ohne erfundene Zahl geht:
  SCHWACH  "so google knows which jobs to show you for"
  STARK    "so the exact job you do finds keygen instead"
  SCHWACH  "worth switching on while you're in there"
  STARK    "so the 2am lockout goes to one of them"
Der Name des Nachbarn darf stehen -- er kommt aus `details.nearest`, ist also gemessen,
und er macht den Verlust konkret statt allgemein. Wo kein Nachbar passt: was es KOSTET
("so it's the profile costing you the calls, not the reputation").

───────────────────────────────────────────────────────────────────────────────
DIE ACHT FORMREGELN, alle am 30.07. an elf echten Mails gelernt.

(a) HANDLUNG UND NUTZEN, NICHT MANGEL.
    statt   "nothing under services, so google has one word to go on"
    lieber  "put your services in so google can match a search against them"
    Wo er eine Staerke hat, wird sie der Hebel, statt eine eigene Lob-Zeile zu bekommen:
      "add emergency locksmith, you're open 24 hours so those 2am searches are yours"
    In einer Vierer-Liste ist eine Zeile ohne Handlung eine verschenkte. Erlaubt ist als
    Ausnahme die Zeile, die die URSACHE benennt, weil auch die eine Handlung impliziert:
      "135 reviews and still second, so it's the profile and not the reputation"

(b) EIN GEDANKE JE ZEILE. Zwei Zahlen nur, wenn die zweite den Satz verdient.
    ZU DICHT "you tend the profile more than most here, 43 photos against a median of
              13 and 7 of your 8 reviews answered, and it's still filed under locksmith"
    BESSER   "43 photos up and nearly every review answered, still just filed locksmith"

(c) UNSERE WOERTER RAUS. Verboten: median, listing, trust signal, category slots,
    visibility, optimise. Er sagt "most uk locksmiths", nicht "the town median".
    Und die Folge in SEINER Sprache:
      statt   "it costs you visibility"
      lieber  "that's the 2am call gone"

(d) JEDER VERGLEICH GEHT GEGEN DAS LAND, NIE GEGEN DEN ORT.
    Erlaubt   "where most uk locksmiths have 20"
    Verboten  "where the rest of reading has 17" · "only 3 of the 11 here post"
              "your 30 reviews put you 4th in bedford"
    GRUND: wir kennen den Ort nur ausschnittsweise -- in Bedford 11 von 27, in Hornchurch
    1 von 20 (der Scrape nahm nur Betriebe mit Website und suchte je Grafschaft). Eine
    Aussage ueber EINEN Nachbarn haelt das aus, der ist gemessen und im Median 900 m weg.
    Eine Aussage ueber ALLE im Ort ist geraten, und der Inhaber kennt seinen Ort besser.
    Die Landeszahlen stehen im Blatt unter `land`:
      Bewertungen  median 20 (n=4.746)      Fotos     median 14 (n=4.746)
      24 Stunden   53% haben es (n=4.530)   Beitraege 67% posten nie (n=3.534)
    Statt eines Rangs im Ort geht der Rang im Land: "your 135 reviews put you in the top
    25% of uk locksmiths" (ab 72) oder "top 10%" (ab 166).

(e) KEIN BEZUG, DEN DER LESER ERST AUFLOESEN MUSS. Nenn die Sache beim Namen:
    UNKLAR  "and the profile that promise sits on just says locksmith"
    KLAR    "and your profile still just says locksmith, nothing else"
    Jede solche Konstruktion verlangt, dass er zwei Dinge im Kopf verbindet, bevor der
    Satz Sinn ergibt. In einer Mail von einem Fremden tut er das nicht.

(f) KEIN BILD, KEIN WORTSPIEL, KEINE METAPHER (ab 22.08.). Sie lesen sich gut und sagen
    nichts, was er tun kann:
    SCHIEF  "3 categories are set, so the frame is there and everything inside is empty"
    KLAR    "3 categories set and nothing under services, put five in"
    SCHIEF  "start and the spot you're holding looks looked-after"
    KLAR    "start posting and the profile looks as busy as you are"

(i) ER WEISS NICHT, WAS EIN GOOGLE BUSINESS PROFILE KANN (ab 22.08.). Er hat es einmal
    angelegt und nie wieder angefasst. Eine Handlung, die voraussetzt, dass er die
    Oberflaeche kennt, ist fuer ihn keine Handlung. Also: sag WO es steht, wenn es nicht
    offensichtlich ist, und benutze das Wort, das dort auch draufsteht.
    UNKLAR  "switch yours on so the 2am jobs come"       (was einschalten? wo?)
    KLAR    "set your hours to 24 hours so the 2am jobs come to you"
    UNKLAR  "add it so that search finds you"            (wohin?)
    KLAR    "add it under services so that search finds you"
    UNKLAR  "fill the rest so more searches find you"
    KLAR    "add the other categories so more searches find you"
    Der Test: koennte er nach dem Lesen die Handlung ausfuehren, ohne jemanden zu fragen?

(g) JEDE ZEILE IST EIN GANZER SATZ, mit Subjekt und Verb. Eine Nominalphrase liest sich
    wie ein Notizzettel:
    FRAGMENT "43 photos and nearly every review answered, so it isn't effort"
    SATZ     "you've got 43 photos up and answer nearly every review, so it isn't effort"
    Der Trick ist immer derselbe: "you've got", "you're on", "there's", "your X puts you".

(h) EIN SATZ JE STICHPUNKT, und casual. Kein Punkt mitten in der Zeile -- zwei Saetze in
    einem Stichpunkt lesen sich wie ein Absatz, der sich verlaufen hat. Verbunden wird mit
    "so", "but", "and", "because".

───────────────────────────────────────────────────────────────────────────────
WELCHE Zeilen kommen, entscheidet die Lage, nicht das Gefuehl (`knowledge/
local-seo-method.md`). `pool.py` setzt das um -- du darfst es nicht unterlaufen.

  NICHT in den drei -> Sichtbarkeit. Dort bewegen nur drei Dinge etwas: Kategorien (bis 10
    erlaubt, die meisten nutzen 1), die Leistungsliste (Ziel 20-30, die meisten haben 7-8),
    und die Bewertungen ("count and recency are among the strongest map-pack signals").
    Fotos, Beitraege und Buchungslink stehen dahinter.
  IN den drei -> was nach dem Klick passiert. Fotos zuerst (das Erste, was er sieht),
    beantwortete Bewertungen, sichtbare Oeffnungszeiten.

Zwei Zeilen sind je Lage VERBOTEN, nicht nur schwaecher:
  "deine Bewertungszahl liegt unter dem Median" an jemanden, der in den drei steht --
    das widerspricht seiner eigenen Position.
  ein Rat zur HAUPTkategorie an jemanden, der rankt -- die Quelle sagt ausdruecklich
    "only swap primary if they are NOT ranking".

───────────────────────────────────────────────────────────────────────────────
DIE FUENF VERBOTE
  1  Keine Zahl, die nicht im Auftrag steht.
  2  NICHT RECHNEN. Keine Differenz, keine Summe, kein Durchschnitt. Braucht ein Satz eine
     abgeleitete Zahl, steht sie schon fertig im Auftrag. (Ein Modell schrieb "you need 8
     more reviews to hit the median" ueber einen Betrieb MIT 8 bei Median 19 -- die Zahl
     stand im Brief, der Satz war trotzdem falsch.) Beide Zahlen nennen, die Differenz nie.
  3  Keine Prozentangaben, die nicht im Auftrag stehen.
  4  Kein Angebot: kein "we handle", "we can run", "for clients", "our clients". Der
     einzige erlaubte Hinweis ist "(this can run on autopilot)".
  5  Kein Wort ueber die Website. Wir messen sie nicht.

DER TON
  Alles klein. Gesprochenes UK-Englisch. Kurze Saetze, ein Gedanke, Punkt.
  Kein Em-Dash, keine Gedankenstriche als Satzzeichen -- Kommas und "so" und "and".
  Kein Markdown, keine Sternchen, keine Ueberschriften.
  Verbotene Fuellwoerter: actually, simply, just, really, truly, essentially,
  "the one thing that matters", "at the end of the day".
  KEIN Raeuspern: nicht "overall", nicht "first off", nicht "in short".
  Nicht alle Zeilen duerfen gleich anfangen -- `verify_mail` verwirft drei gleiche Anfaenge.
  Gelegenheiten, keine Vorwuerfe. Auch beim Erstplatzierten kein Tadel.
```

## Geprueffte Plattform-Zahlen

> Nur was hier steht, darf als Plattform-Grenze in eine Mail. Eine erfundene Grenze ist der
> teuerste Satz der Kampagne: sie klingt nach Fachwissen und ist in Sekunden widerlegt.
> Neue Zahl gefunden? Erst belegen, dann hier eintragen, dann verwenden.

| Zahl | Was sie bedeutet | Beleg |
|---|---|---|
| **10 Kategorien** | 1 Hauptkategorie plus bis zu 9 weitere | mehrfach belegt, und die meistbelegte Zeile unserer Bedford-Kohorte fuehrt 9 (Timpson) — konsistent |

**Bewusst unbelegt, auf Lukas Entscheidung (30.07., dritte Ansage):** "the top 3, which is
where over half of all business goes to". Fuer KLICKS auf den Local Pack gibt es kursierende
Studien, fuer AUFTRAEGE oder Umsatz hat es niemand gemessen. Mein Einwand steht hier, damit
ihn niemand fuer ein Versehen haelt und ihn beim naechsten Lesen wieder "korrigiert": ein
Betrieb, der die Haelfte seiner Auftraege ueber Stammkunden macht, kontert den Satz aus dem
Stand. Die Sperre in `verify_mail.py` ist dafuer ausgebaut worden. Wird die Zahl je belegt,
gehoert sie in die Tabelle oben; bis dahin ist sie die EINE bewusste Ausnahme.

**Nicht belegt und deshalb verboten:** eine Zahl fuer Service-Felder. Luka hat „20" ins
Gespraech gebracht, ich habe keinen Beleg gefunden. Bis einer da ist, heisst es „your
services list", nicht „20 service fields".

---

## Die Regeln, an die sich der Schreiber haelt

> **Diese Regeln sind der Prompt.** `write_mail.py` liest den folgenden Codeblock zur
> Laufzeit aus dieser Datei und haengt ihn an sein System-Prompt. Wer hier etwas aendert,
> aendert damit sofort, was Sonnet schreibt -- es gibt keine zweite Fassung im Python.
>
> Der Grund (Luka, 27.07.: "aenderst du jetzt das Agent-Prompt oder Skill-Prompt?"): der
> Rahmen stand schon hier, die Regeln standen im Python. Zwei Orte fuer dieselbe Sache sind
> genau die Konstellation, aus der heute schon einmal Drift entstanden ist.

```
HARD RULES, in order of importance:
- Use ONLY facts from the brief. Never introduce a number, a comparison, a competitor or a
  claim that is not in it. If you are unsure whether something is in the brief, leave it out.
- NEVER do arithmetic. Do not subtract, add, average or work out a difference. Haiku wrote
  "you need 8 more reviews to hit the median" about a business that HAS 8 reviews against a
  median of 19. The number was in the brief and the sentence was still false. State a number
  the way the brief states it, or leave it out.
- Attribute every comparison to the right pool. A uk median is not a town median. If the
  brief says "uk", the sentence says "uk".
- Plain text only. No markdown, no asterisks, no headings, no labels. If a line ends in
  a colon and could be a section title, it is one, and it comes out.
- The fix list names WHAT WOULD CHANGE and WHAT HE GETS, never the how-to (Luka, 27.07.:
  "bei den negativen mehr in die Richtung Liste, was man aendern wuerde und welchen
  positiven Effekt das haette"). The difference is the whole business model:
      how-to (never)   "go into your profile, open opening hours, tick 24 hours"
      deficit (no)     "no opening hours set, so the 2am lockout can't tell if you'll answer"
      effect (yes)     "opening hours on the profile would put you in front of the 2am
                        lockout, right now that call goes to someone else"
  EACH LINE OPENS WITH THE CHANGE, not with what is missing. Same fact either way, but
  "dir fehlt X" is a list of failings from a stranger and "X would get you Y" is something
  worth doing. The missing part still gets named, it just comes second.
  He can act on the second one only by knowing WHAT to change, and he still needs the
  report to know how and in what order. A cold email that hands over the instructions has
  solved his problem for free and removed the reason to reply.
- Never state a cause we did not measure. "your profile is missing X" is fine. "that is why
  you rank below Y" is not, unless the brief says so.
- Everything lowercase, the way people type in a hurry. Exception: words quoted from their
  own website keep their original spelling exactly.
- No dashes of any kind as punctuation. Use commas, full stops, "so", "and".
- No adjectives propping up a number. "135 reviews" carries itself; "impressive 135 reviews"
  weakens it.
- AT MOST THREE NUMBERS IN THE OPENING PARAGRAPH. Die Aufgabenzeilen zaehlen NICHT
  mit: jede traegt ihre eigene Belegzahl, und die ist dort der ganze Punkt. Der
  Deckel galt urspruenglich fuer die ganze Mail und war damit unerfuellbar, sobald
  vier Zeilen mit je einer Zahl dastanden. This is the rule people break first. One
  draft opened with "1328 reviews puts you first out of 11 locksmiths in bedford and in the
  top 1% of uk locksmiths against a uk median of 19" - six numbers in two sentences, every
  one of them true, and nobody reads it.
  For a single fact, keep the COMPARATIVE number and drop the raw one. He already knows he
  has 1328 reviews; what he does not know is that it makes him first in town. "you've got
  more reviews than anyone else in bedford, and that puts you in the top 1% nationally"
  beats the version above.
  NEVER drop a comparison down to an adjective. "way more photos than the typical listing"
  and "a middle of the pack that sits nowhere close" are what happened when this rule was
  first written, and both are worse than the number-heavy version: they cannot be checked,
  so they read as sales talk. If a comparison is worth making, it keeps its number.
- HIS OWN NUMBER IS THE SUBJECT, NEVER THE NEWS. He knows he has 43 photos. What he does
  not know is where that puts him. So the number stays in the sentence and stops being the
  announcement:
      bad   "you've got 43 photos on the profile, against a middle of the pack at 14"
      good  "your 43 photos put you above every other locksmith in bedford"
      good  "your 135 reviews put you second in town"
  The pattern is: "your {his number} {verb} {where it lands him}".
  DELETING HIS NUMBER IS NOT THE FIX. When this rule was first written the model removed it
  instead and produced "your photos comfortably clear bedford's typical count" and "your
  profile's photo count puts you well above the typical listing" - vague, unverifiable, and
  it smuggled back the propping adjectives. Keep the number, turn the sentence around.
- THE MOOD STAYS POSITIVE. This is a note to someone who runs a business, not a fault
  report (Luka, 27.07.: "ich mag die Mails nicht, die die ganzen schlechten Sachen
  hervorheben, wir wollen die Stimmung positiv halten"). Concretely:
    * The fix list is a TO-DO LIST, not a fault list. THREE TO FOUR lines, never five
      (Luka, 27.07.: "5 Punkte ist zu viel"). Bei fuenf kippt die Liste von "ein paar
      Sachen fuer heute Nachmittag" zu einer Pruefliste, und genau das soll sie nicht
      sein. Der schwaechste von fuenf Punkten zieht ausserdem die vier starken mit
      runter. Lieber vier, die sitzen. Jede Zeile ist ein
      afternoon's work. It reads like something a mate who knows this stuff would jot down,
      and that is exactly why it opens with the Einstiegszeile unten.
    * DIE EINSTIEGSZEILE NENNT, WIE VIEL WIR GEPRUEFT HABEN (Luka, 27.07.: "ich dachte im
      Introsatz vor der Stichpunktliste erwaehnen wir auch, wie viele Dimensionen wir
      analysiert haben"). Sie kommt aus Python, nie vom Modell, und die Zahl ist die
      SUMME DER GEMESSENEN Faktoren dieses Leads (`profile.met` + `site.met` aus dem
      Brief), nicht der Katalog. Bei einem Lead mit 2 von 7 Profil- und 9 von 12
      Website-Faktoren:
          "i went through 11 things across your profile and site. these few are worth an
           afternoon:"
      Zwei Dinge auf einmal: sie belegt, dass gerechnet wurde, und sie baut den Kontrast
      zu den 71 Checks im Angebot auf, der sonst aus dem Nichts kommt. Die alte Fassung
      ("a few things on your google profile you could do this afternoon:") war ausserdem
      FALSCH, sobald ein Website-Tipp in der Liste stand, und das war der Normalfall.
      Five opportunities land differently from five failings, and the only difference is
      how each line starts.
    * Every one of them is an OPPORTUNITY he has not taken yet, not a mistake he made.
      "listing emergency locksmith would put you in front of those searches" is the same
      fact as "you are not listed as emergency locksmith", and one of them makes him want
      to do something.
    * Assume he is good at his trade and busy. The gaps exist because he was out on jobs,
      not because he was careless, and the writing should sound like someone who knows that.
    * Never imply he is behind, losing, failing or falling short. He can be "not yet in
      front of" a search. He is never "invisible", "nowhere" or "missing out".
    * The last thing he reads before the offer is the verdict. It names the imbalance
      without a verdict on HIM.
- KLEINE HINWEISE, DIE ZEIGEN WAS WIR TUN. Hoechstens EINER je Mail, in Klammern, hinter
  der Zeile, zu der er passt. Er verkauft nichts, er laesst nur durchblicken, dass es fuer
  diese Arbeit jemanden gibt:
      "- start posting, only 4 of the 11 here do (this can be fully automated btw)"
- UEBER DIE WEBSITE WIRD NICHTS BEHAUPTET, WAS WIR NICHT GEMESSEN HABEN (Luka, 27.07.:
  "ich finde wir sind was die Website angeht viel zu confident, wir testen ja wirklich nur
  ein bisschen was" / "normalerweise ist die Website bei diesen Businesses ja auch
  Schrott"). Was wir pruefen, sind zwoelf Markup-Punkte auf der STARTSEITE: Viewport,
  Title, Schema, Karte, Sprache, tap-to-call und aehnliches. Kein Tempo, keine Inhalte,
  kein mobiles Rendering, keine Indexierung, keine Unterseiten.
  Gemessen an 3.299 Leads: Median 84, und **81 % erreichen 70 oder mehr**. Das Profil
  dagegen: Median 64, nur 39 % ueber 70.
    * VERBOTEN sind Saetze ueber die Website ALS GANZES: "your website holds up well",
      "your site is in great shape", "the site's carrying its weight". Vier von fuenf
      Empfaengern bekaemen dasselbe Lob, und der Inhaber weiss selbst am besten, was seine
      Seite taugt. Es ist die EINZIGE Aussage der Mail, die er aus eigener Anschauung
      pruefen kann -- widersprechen wir ihm dort, glaubt er auch die Profil-Befunde nicht
      mehr, und die sind belastbar.
    * ERLAUBT ist der eng gefasste Befund: "the basics on your homepage are in place",
      "the markup on the homepage is mostly there". Er sagt, was geprueft wurde, und
      verspricht nichts darueber hinaus.
    * Der Lage-Absatz fuehrt NIE mit der Website als Staerke. Er fuehrt mit der Marktlage
      (Bewertungen, Fotos, Rang in der Kohorte) oder mit dem Profil.
    * NACHTRAG 27.07., ABENDS: die Website wird gar nicht mehr gemessen. Der HTML-Scrape
      ist raus (PIPELINE.md § 0a) -- 13 Markup-Pruefungen, die 81% der Leads bestanden,
      also nichts unterschieden, und die die einzige Aussage produziert haben, die ein
      Empfaenger aus eigener Anschauung widerlegen kann. Damit gilt schaerfer als vorher:
      **ueber die Website steht NICHTS in der Mail**, weder Lob noch Mangel. Die einzige
      Ausnahme ist die tote Domain, und die kommt aus einer DNS-Abfrage, nicht aus einem
      Scrape: "the site on your profile does not load at all". Alles andere ueber die
      Seite gehoert in den Report, und der ist das Angebot.
- DER LAGE-ABSATZ IST PROSA, KEINE KOPFZEILE (Luka, 27.07.: "das hier finde ich noch ein
  bisschen abrupt und nicht so elegant geschrieben"). Zwei Fehler machten ihn abrupt:
    * Er begann mit einer nackten Zahl ohne Verb. "6 reviews against a uk median of 20."
      ist kein Satz, sondern eine Bilanzzeile. Die Zahl gehoert IN einen Satz ueber den
      Betrieb: "you've got 6 reviews where the uk median is 20". Der Absatz faengt beim
      Betrieb an, nie bei der Ziffer.
    * Er zaehlte die Maengel auf, die zwei Zeilen tiefer als Liste stehen. "...not the
      site, no opening hours and no posts" nimmt der Liste ihre Arbeit weg und liest sich
      wie ein Register. Womit genau, steht darunter.
  ABGELOEST AM 27.07.2026, ABENDS. Der Absatz sagte bis dahin, WELCHE SEITE duenner ist --
  Profil oder Website. Es gibt keine Website-Seite mehr (der HTML-Scrape ist raus, siehe
  § 0a in PIPELINE.md). An seine Stelle treten ZWEI Saetze:

    SATZ 1, DIE POSITION. Wo er steht, aus genau EINER Rangliste.
      "when someone in bedford searches for a locksmith, you're the first of the three
       google shows."
      "google shows three locksmiths when someone searches in bedford, and you're not one
       of them. in maps you come up 11th."

    SATZ 2, DER WIDERSPRUCH. Zwei Zahlen nebeneinander, die nicht zusammenpassen.
      "the one above you has 8 reviews. you've got 107."
    Er ist der Grund, warum die Liste darunter gelesen wird: Satz 1 allein ist eine Zahl,
    mit der er nichts anfangen kann. Satz 2 macht daraus eine Frage -- WARUM steht der
    ueber mir -- und die Liste ist die Antwort. Ohne ihn ist die Liste eine Maengelliste.

  DIE ZWEI RANGLISTEN WERDEN NIE GEMISCHT. Local Pack sind die drei Kaesten ueber den
  blauen Links bei google.com, Maps ist die Liste in der App. Gemessen an Bedford stimmte
  nur Platz 1 ueberein. Wer im Pack Erster ist, hat dort NIEMANDEN ueber sich, auch wenn
  er in Maps Dritter waere -- am 27.07. entstand daraus "du bist Erster" direkt neben
  "shepard steht ueber dir", beide Saetze wahr, zusammen Unsinn. Der Brief gibt deshalb
  `position.fuehrt_mit` vor; diese Liste gilt, die andere wird nur erwaehnt, wenn sie
  ausdruecklich als die andere benannt wird ("third in the pack, but first in maps").

  GIBT ES KEINEN WIDERSPRUCH, WIRD KEINER ERFUNDEN. Bei einem Erstplatzierten steht
  niemand ueber ihm, und es wird auch keine Konkurrenz erfunden.

  DER ERSTE BEKOMMT EINEN ANDEREN RAHMEN: VERTEIDIGEN, NICHT VERBESSERN (Luka, 27.07.:
  "wenn sie Erster sind, muessen wir das reframen -- du bist Erster und so kannst du das
  verteidigen"). Wer vorne steht, will nicht gewinnen, sondern nicht verlieren, und das
  ist der staerkere Antrieb. Die relevante Zahl ist deshalb nicht seine eigene Luecke,
  sondern der VERFOLGER:
      "you're first of the three google shows in bedford. the one behind you is 12
       reviews away."
  Das ist der Spiegel des Widerspruchs: statt "wer steht ueber dir und ist schwaecher"
  gilt "wer steht hinter dir und wie nah". Der Brief liefert dafuer `verfolger`.

  Und die Liste dreht mit. Dieselben Befunde, andere Begruendung:
      statt  "add emergency locksmith, those searches go to someone else"
      dann   "add emergency locksmith, it is the one search where the gap to second
              closes fastest"
  Kein Tadel, kein "dir fehlt". Es ist ein Vorsprung, den man ausbauen oder verlieren
  kann. Der Verdict benennt entsprechend nicht eine Schwaeche, sondern was den Vorsprung
  traegt und was ihn kosten wuerde.

  Hat der Erste keinen greifbaren Verfolger (die Zahl fehlt, oder der Abstand ist so
  gross, dass "verteidigen" laecherlich klingt), folgt auf Satz 1 die auffaelligste Zahl
  aus den Befunden -- gern eine im Kontrast zur Spitzenposition ("1328 Bewertungen, und
  auf keine geantwortet").

  WETTBEWERBER WERDEN NUR BENANNT, WENN WIR IHREN NAMEN SELBST HABEN. Die Rangliste
  liefert abgeschnittene Titel; "shepard locksmith colcheste" stand so in einer Mail.
  Steht der Betrieb in unserem Bestand, gilt UNSER Name. Sonst heisst es "the one above
  you".
- DIE STICHPUNKTE DUERFEN NICHT ALLE GLEICH GEBAUT SEIN (Luka, 27.07.: "wir haben zu eine
  aehnliche Satzstruktur, immer x would do y"). Gemessen an einer echten Mail: vier von
  fuenf Zeilen liefen als "[-ing] ... would [Verb]". Das kommt daher, dass "beginnt mit
  einem Verb" fuer sich genommen zur Gerundium-Schleife fuehrt. Deshalb: HOECHSTENS ZWEI
  Zeilen je Mail duerfen dieselbe Bauform haben. Es gibt drei, und sie sind alle erlaubt:
      Aufforderung + Folge   "switch on 24 hour opening, and the 2am call stops going
                              to the other 7"
      Beobachtung + Folge    "your profile has no photos, so it looks thin next to the rest"
      Vergleich zuerst       "only 2 of the 11 here post, and google reads a still
                              profile as an untended one"
  Alle drei bleiben Gelegenheiten, keine Vorwuerfe. Die Bauform wechselt, der Ton nicht.
- UND SIE DUERFEN NICHT ALLE DASSELBE ARGUMENT FAHREN (Luka, 27.07.: "da koennen wir mehr
  variieren zwischen Vergleichen mit einem Wettbewerber, benefit-orientiertem Schreiben,
  Notiz dass der Prozess automatisierbar ist"). Bauform ist die Verpackung, der Blickwinkel
  ist das Argument. Eine Mail mischt MINDESTENS ZWEI der vier:
      Kohorten-Vergleich   was die Nachbarschaft tut und er nicht: "only 2 of the 11 here
                           show 24 hours". Traegt die Zahl, die er nirgends nachsehen kann.
      Einzelner Nachbar    ein Wettbewerber beim NAMEN, aus details.nearest: "lockforce
                           down the road lists eleven services, your profile lists one".
                           Der schaerfste Blickwinkel, weil er konkret ist. Nur mit einer
                           Zahl, die wir zu diesem Nachbarn wirklich haben.
      Nutzen fuer ihn      was er DAVON hat, nicht was fehlt: "adding emergency locksmith
                           puts you in for the 2am lockout nobody shops around for".
                           Mindestens eine Zeile je Mail faehrt diesen Blickwinkel.
      Automatisierbar      der Hinweis in Klammern, hoechstens EINER je Mail (siehe oben).
  Vier Zeilen Kohorten-Vergleich hintereinander sind so ermuedend wie vier gleiche
  Satzanfaenge, auch wenn jede fuer sich stimmt.
      "- add your services, google matches on those words (we do this in bulk)"
  Nur an einer WIEDERKEHRENDEN Aufgabe. Niemand automatisiert eine Kategorie, die er
  einmal in fuenf Minuten setzt, und der Hinweis daneben wirkt dann aufgesetzt. Zwei
  solcher Klammern in einer Mail sind eine Verkaufsmail.
- SHORT SENTENCES. One idea, full stop, next idea. Around 15 words, never more than 20.
  This is the single biggest tell that a machine wrote it, and it was the last thing left:
      bad   "your photos are the one thing that clearly sets you apart in bedford, 43 of
             them, good enough for 4th in town, and your website is doing the heavy lifting
             too, ticking nearly every box we check while the google profile lags well
             behind it."
      good  "43 photos, fourth most in bedford. your site is solid too, nearly everything
             we check is there. the profile is the weak one."
  Same facts, three sentences instead of one, twenty words shorter.
- BANNED PHRASES, because they are padding and every one showed up in a draft:
  "doing the heavy lifting", "ticking every box", "lags behind", "jumps out", "stands out",
  "worth pointing out", "the one thing that", "straight away", "actually", "clearly",
  "properly", "real work", "the real drag". Cut one and the sentence still says the same
  thing? Then it was padding.
- Casual means FEWER words, not friendlier ones. A tradesman texts in fragments. "no map on
  the site" is a complete thought. It does not need "there is currently no map present on
  your website".
- A MIDDLE IS NOT A TOP. "above the middle of the pack" never becomes "above everyone".
  This produced a checkable falsehood: the brief said "43 photos against a middle of the
  pack at 14" and the mail said "above every other locksmith in bedford" -- 43 is FOURTH,
  the leader in that town has 1219. If the brief does not say first, you do not say first.
  Same for "the most", "nobody else", "top of the pack".
- If you announce a count, the list has exactly that many lines. "three things i'd fix"
  followed by four is the kind of slip a reader notices and nothing else in the mail
  recovers from.
- Speak in jobs and phone calls, not in marketing terms. An owner thinks about the 2am
  call, not about "entity signals" or "schema markup". Translate every technical factor.
- The praise part: 25 to 45 words. The fix part: 40 to 60. Any sentence that carries
  neither a comparison nor a consequence comes out.
```

---

## The rules the copy has to obey

1. **Benefit-driven, never mangel-driven.** A finding ends at what it means for them, not at what is
   missing. `the hard part is done` over `your reviews are good`. `that's the work sitting closest to
   you right now` over `you lose those searches`. A tradesman thinks in jobs, not in traffic.
2. **No adjective that props up a number.** `134 reviews at 4.9` carries itself; `impressive 134
   reviews` weakens it by smuggling in opinion.
3. **No conditional on the offer.** `the full report shows` — it exists. `i'd be able to put together`
   does not ship.
4. **Floor at ~130 words.** The work has to stay visible in the text. Below that the same facts read as
   a template with variables again, and the credibility the market claim buys is spent.
5. **"your two closest competitors" goes BEFORE the names, never after.** Trailing it behind the names
   (*"auto keys, gemini lock & safe, your two closest"*) reads as an explanation of something the owner
   knows better than we do. Leading with it (*"your two closest competitors, auto keys and gemini lock &
   safe"*) makes it an introduction, and the names land as proof instead of as a claim. Same words,
   opposite effect.
6. **Get the arithmetic right, the reader can count.**
   `{others_count} = market_count - 1 (the lead) - 2 (the two named)`. Bedford has 12, so the line reads
   *the other 9*, not *the other 12*. The CTA's `{market_count_minus_1}` is a different number (11)
   because there the two named are counted back in.
7. **Use `{company_casual}`, never `{company}`.** The legal name reads like a database dump in the
   middle of a sentence: *"how they compare to Mobile Locksmith Domestic and Auto Ltd"* is not a thing a
   person types. `casualize.py` already produces the short form. With `{first_name}` at 0% coverage this
   is also the only personal token in the mail, so it has to sound like a person said it.
8. **Every comparative line must be data-gated.** `only auto keys is ahead of you` is true here only
   because it was checked against all 12 Bedford businesses. An earlier draft claimed the lead beat both
   competitors on reviews; Auto Keys has 1,293 against their 134. Ungated across 3,000 leads that is
   automated reputational damage. Same failure as the report's Etappe 1 (journal, same day).

## Open before this ships

- **`{first_name}` is 0% covered** on the 3,161 mailable leads. Either buy the Apify owner-enrichment
  ($5/1000, ~$16 for the list) or fall back to `hey there,`. The personalization does not live in the
  name, it lives in the two competitor names and the market count — start without it.
- **Ein Betrieb ohne Vorsprung bekommt eine Mail mit einem Lob gegen drei Maengel.** Gold Key
  Locks liest sich dadurch wie eine Abrechnung. Der Prompt verbietet ausdruecklich, eine
  gewoehnliche Zahl zur Staerke aufzublasen, also ist die Asymmetrie ehrlich — ob sie
  verkaeuflich ist, ist eine Vertriebsentscheidung und keine technische.

**Erledigt am 27.07.2026:**
- ~~Die Prosa-Variante braucht Kombinationsregeln statt freier Generierung~~ — geloest, aber
  anders als gedacht. Nicht ein Dutzend Satzmuster, sondern: Python liefert geprueffte Fakten
  (`brief.py`), das Modell ordnet sie, und `verify_mail.py` prueft mechanisch nach, dass jede
  Zahl im Brief steht und keine gerechnet wurde. Der Fall, vor dem die Sorge berechtigt war,
  ist beim zweiten Testlead eingetreten: „you need 8 more reviews to hit the town median" bei
  einem Betrieb mit 8 Bewertungen und einem UK-Median von 19. Der Pruefer hat ihn gefangen.
- ~~25% der Leads tragen weniger als zwei Positive~~ — kein Fallback noetig. Das Modell
  bekommt den vollen Brief und schreibt, was da ist; steht nichts heraus, sagt es das.

## Reading the test

Split 50/50 across the list. Measure **positive replies**, not replies — "not interested" is a reply.
At ~1,600 per arm and a mid-single-digit reply rate the test can resolve a difference of roughly two
percentage points, not a subtle one. If the two land within a point of each other, the format does not
matter and the winner is whichever is cheaper to generate reliably, which is B.

The hypothesis worth holding: B is scannable on a phone between two jobs, A reasons and therefore
proves attention. Tradesmen read on phones. A is the better copy; B may still win.
