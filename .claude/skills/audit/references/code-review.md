# Code-Urteil: geerbte Kriterien

Gelesen, wenn `/audit` über ein einzelnes Repo urteilen soll — also wenn der Nutzer nach dem Bericht sagt „schau dir X genauer an". **Nicht** im Standardlauf: die Code-Kachel misst dort nur mechanisch (README, uncommittete Arbeit, ruhende Repos) und liest keinen Code.

## Zwei Quellen, beide ohne API

**Erste Quelle: was als echter Befund zählt.** Aus Anthropics `claude-code-security-review` (liegt unter `projects/_external/claude-code-security-review/`, die Substanz in `claudecode/claude_api_client.py` und `claudecode/findings_filter.py`) stammt die Ausschlussliste weiter unten.

**Das Python dort wird nicht ausgeführt.** Es ruft die Anthropic-API direkt (`ANTHROPIC_API_KEY` ist Pflicht, sonst bricht der Client ab) und ist auf Pull-Request-Diffs zugeschnitten, nicht auf Ordner. Beides passt nicht: die API würde zusätzlich zur Subscription abgerechnet für ein Urteil, das in der Session mit denselben Kriterien fällt, und ein Ordner ist kein Diff.

**Was wir übernehmen, ist das Wertvolle daran:** eine erprobte Liste von Fehlalarm-Mustern. Genau daran scheitern Prüfwerkzeuge sonst — nicht am Finden, am Nicht-Melden.

**Zweite Quelle: wie man zu einem sicheren Urteil kommt.** Das Plugin `code-review` (`~/.claude/plugins/cache/claude-plugins-official/code-review/`) macht es ohne API, komplett mit Sub-Agenten, und sein Aufbau ist übertragbar:

- **Mehrere Blickwinkel parallel statt eines gründlichen Durchgangs.** Dort: Einhaltung der CLAUDE.md · flacher Bug-Scan nur auf den Änderungen · git-Historie des betroffenen Codes · frühere Anmerkungen zu denselben Dateien · Code-Kommentare als Vorgabe. Ein einzelner Durchgang findet systematisch weniger, weil er nur eine Frage stellt.
- **Danach eine getrennte Confidence-Runde.** Jeder Fund wird von einem eigenen, billigen Agenten auf 0 bis 100 bewertet — 0 heißt „hält keiner leichten Prüfung stand", 100 heißt „direkt belegt". **Alles unter 80 fliegt raus.** Dass der Prüfer nicht derselbe ist wie der Finder, ist der Punkt: wer etwas gefunden hat, will es behalten.
- **Seine Fehlalarm-Beispiele gelten hier genauso:** vorbestehende Probleme · was wie ein Bug aussieht aber keiner ist · Kleinigkeiten, die ein erfahrener Entwickler nicht ansprechen würde · alles was Linter, Typechecker oder Compiler ohnehin fangen · allgemeine Qualitätsthemen wie fehlende Tests, außer die CLAUDE.md verlangt sie ausdrücklich.

**Warum wir es trotzdem nicht direkt aufrufen:** `/code-review` arbeitet auf einem Pull Request (`gh pr diff`), nicht auf einem Ordner. Für ein einzelnes Repo mit offenem PR ist es der richtige Befehl und wird empfohlen. Für das Ordner-Audit ist die Form falsch, die Methode aber richtig.

## Vorgehen

Drei Phasen, in dieser Reihenfolge:

1. **Kontext verstehen.** Welche Sicherheits-Bausteine benutzt das Repo schon (Framework, Validierung, Auth)? Was ist sein Bedrohungsmodell? Ohne das bewertet man Muster statt Risiken.
2. **Vergleichen.** Weicht neuer Code von den etablierten Mustern des Repos ab? Abweichung ist das stärkste Signal, stärker als jede Musterliste.
3. **Bewerten.** Datenfluss von der Eingabe bis zur sensiblen Operation verfolgen. Wo werden Vertrauensgrenzen überschritten?

## Schweregrade

- **hoch** — direkt ausnutzbar: Codeausführung, Datenabfluss, umgangene Authentifizierung
- **mittel** — braucht bestimmte Bedingungen, hat dann aber echte Wirkung. **Nur melden, wenn offensichtlich und konkret**
- **niedrig** — Tiefenverteidigung. Im Zweifel weglassen

**Confidence unter 0,7 wird nicht gemeldet.** Die Probe: Ist ein konkreter Angriffsweg benennbar, oder ist es ein Muster, das theoretisch gefährlich aussieht?

## Die Ausschlussliste

Das Herzstück. Diese Dinge werden **nicht** gemeldet, auch wenn sie auffallen:

**Grundsätzlich draußen**
- Denial of Service, Ressourcen-Erschöpfung, fehlendes Rate Limiting, Speicher- oder CPU-Verbrauch
- Fehlende Härtungsmaßnahmen. Code muss keine Best-Practice-Sammlung erfüllen, nur offensichtliche Lücken vermeiden
- Veraltete Fremdbibliotheken. Das wird anderswo verwaltet
- Dateien, die ausschließlich Tests sind
- Abstürze, die keine Verwundbarkeit sind (undefinierte Variable ist kein Sicherheitsproblem)
- Fehlende oder veränderbare Audit-Logs
- Ressourcen-Lecks (Speicher, Dateideskriptoren)

**Trotz gefährlichem Aussehen harmlos**
- Umgebungsvariablen und CLI-Flags sind **vertrauenswürdig**. Ein Angriff, der voraussetzt sie zu kontrollieren, ist keiner
- UUIDs gelten als nicht erratbar und müssen nicht validiert werden
- React ist gegen XSS grundsätzlich sicher — außer bei `dangerouslySetInnerHTML` und Verwandten
- Client-seitiger TypeScript-Code braucht keine Rechteprüfung. Das ist Sache des Servers. Dasselbe gilt für alles, was Daten an ein Backend schickt
- SSRF und Path-Traversal in Client-Code (`.js`, `.ts`, `.tsx`) sind ungültig — Client-Code erreicht keine internen Ressourcen
- SSRF, das nur den Pfad kontrolliert, ist keins. Nur Host oder Protokoll zählen
- `../` in HTTP-Anfragen ist meist unkritisch. Relevant wird es beim Dateilesen
- Nutzereingaben in KI-Prompts sind an sich keine Verwundbarkeit
- Log-Spoofing durch unsanitiertes Echo ist keine Verwundbarkeit. Logging von URLs gilt als sicher, Logging von Request-Headern als gefährlich (Zugangsdaten)
- Logging nicht-personenbezogener Daten ist keine Verwundbarkeit, auch wenn die Daten sensibel wirken. Gemeldet wird nur, was Geheimnisse, Passwörter oder personenbezogene Daten offenlegt
- Command Injection in Shell-Skripten nur mit konkretem Weg für fremde Eingaben — Shell-Skripte laufen selten mit fremdem Input
- Verwundbarkeiten in GitHub-Action-Workflows und Notebooks nur mit sehr konkretem Angriffsweg
- Subtile Web-Themen: Tabnabbing, XS-Leaks, Prototype Pollution, Open Redirects
- Race Conditions und Timing-Angriffe, außer sie sind wirklich gravierend
- Speichersicherheit in Rust (gibt es dort nicht)

**Doch drin:** Geheimnisse im Klartext zu loggen ist eine Verwundbarkeit.

## Ausgabe

Je Befund: Datei und Zeile · Schweregrad · Kategorie · was passiert · **konkretes Angriffsszenario** · was dagegen hilft · Confidence.

Das Angriffsszenario ist der Filter. Wer es nicht konkret hinschreiben kann, hat keinen Befund, sondern ein ungutes Gefühl.

**Der Leitsatz:** Lieber ein theoretisches Problem übersehen als den Bericht mit Fehlalarmen fluten. Jeder Befund muss etwas sein, das ein erfahrener Mensch in einem Review ohne Zögern ansprechen würde.
