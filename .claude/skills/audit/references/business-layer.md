# Die Betriebs-Ebene

Gelesen in Schritt 5 von `/audit`, **nur wenn der Nutzer zugestimmt hat oder `context/profile.md` schon existiert**. Hier steht das kurze Interview, die Ableitung des Soll-Profils, die Bewertung der genutzten Werkzeuge und das Urteil über den Werkzeugkasten als Ganzes.

Diese Ebene ist bewusst optional. In einer Umgebung, in der Werkzeuge von der IT gesetzt werden, ist sie sinnlos — der Ordner-Teil von `/audit` steht für sich.

## Das Interview: sechs Fragen

**Vorbefüllen statt fragen, wo die Antwort schon dasteht** — `context/config.yaml`, der „Who I Am"-Abschnitt der globalen `~/.claude/CLAUDE.md`, die Projektnamen in `context/PROJECTS.md`. Vorschlagen, bestätigen lassen. Auf einem fremden Ordner gibt es diese Quellen nicht, dann wird gefragt.

1. **Was machst du, für wen?** Ein Satz. Daraus folgen Betriebsart, Branche, Zielkunde — und ob lokal oder überregional gearbeitet wird (ableiten und still bestätigen, nicht separat fragen).
2. **Wie viele Menschen arbeiten mit, und wer fasst diesen Ordner an?** Allein heißt: geteilte Ablage und Team-Chat sind *irrelevant*, nicht *fehlend*.
3. **Liste alle Werkzeuge, die du täglich nutzt, und wofür jeweils.** Optional: was hast du abgeschafft und warum? Das „wofür" ist der eigentliche Ertrag — es nennt die Aufgabe, an der das Werkzeug gemessen wird, und verrät die Wechselkosten. „War halt schon da" und „unsere ganze Abrechnung hängt dran" führen zu völlig verschiedenen Empfehlungen. Abgeschaffte Werkzeuge verhindern, dass etwas vorgeschlagen wird, das schon durchgefallen ist.
4. **Wo läuft der Kundenkontakt?** Mail, Telefon, WhatsApp, Formular, Plattform.
5. **Was kostet dich gerade am meisten Zeit oder Nerven?** Bis zu drei Dinge. Ohne diese Antwort misst das Audit Vollständigkeit statt Nutzen, und eine Empfehlung ohne echten Schmerz wird nie umgesetzt.
6. **Was soll dieser Ordner tragen, und was ausdrücklich nicht?**

Zu einem Werkzeug ohne erkennbares „wofür" **eine** Rückfrage, nicht mehr. Ziel: unter zwei Minuten. Danach `context/profile.md` schreiben; abgelehnte Vorschläge früherer Läufe stehen dort mit Datum und Grund und werden nicht erneut vorgeschlagen.

## Soll-Profil: welche Fähigkeit zählt für wen

Zwölf Fähigkeits-Slots, die für jeden Betrieb gelten. Jeder bekommt aus dem Profil eine Stufe: **Pflicht · nützlich · irrelevant**.

```
Mail · Kalender · Ablage · Team-Chat · CRM · Buchhaltung/Rechnung
Aufgaben/Projekte · Website/Shop · Social/Publishing · Support-Postfach
Entwicklung · Lokale Sichtbarkeit
```

**Die Zuordnung folgt Regeln aus den Antworten, nie einer Branchentabelle.** Eine feste Zuordnung „Handwerk braucht X" wäre genau der Bias, den dieses Werkzeug vermeiden soll.

| Aus dem Profil | folgt |
|---|---|
| Kundenkontakt läuft über einen Kanal | dieser Kanal wird Pflicht |
| Allein oder zu zweit | Team-Chat und geteilte Ablage irrelevant |
| Lokal, Laufkundschaft oder Einzugsgebiet | lokale Sichtbarkeit Pflicht |
| Wiederkehrende Kunden, Angebote, Nachfassen | CRM Pflicht |
| Rechnungen im eigenen Namen | Buchhaltung Pflicht |
| Code, Deployments, eigenes Produkt | Entwicklung Pflicht |
| Reichweite ist Teil des Geschäfts | Social/Publishing Pflicht |
| Ein Painpoint nennt einen Bereich ausdrücklich | dieser Bereich steigt eine Stufe |

Ein **irrelevanter Slot taucht im Bericht gar nicht auf**. Ein fehlender Pflicht-Slot ist ein Befund, ein fehlender nützlicher eine Anregung.

## Das Dossier: fünf Fragen je genanntem Werkzeug

### 1. Funktionsabdeckung

Deckt es die Aufgaben ab, die aus dem „wofür" **und den Painpoints** folgen? Die Soll-Fähigkeiten werden aus dem Schmerz abgeleitet, nicht aus einer generischen Feature-Liste.

> „Anfragen per WhatsApp gehen verloren" → gebraucht wird ein WhatsApp-Eingang im CRM → kann das genannte Werkzeug das, und ist es eingeschaltet?

### 2. Anbindbarkeit — die Leiter

Immer von oben prüfen, die erste Stufe die trägt gewinnt:

| Stufe | Weg | Aufwand für den Nutzer |
|---|---|---|
| 1 | Connector in Claude Cowork | einmal anmelden, keine Konfiguration |
| 2 | Offizieller MCP-Server (npm oder remote) | Token anlegen, einmal registrieren |
| 3 | CLI | installieren, authentifizieren |
| 4 | REST-API mit eigenem Script | Key besorgen, Script bauen |
| 5 | kein Weg | ehrlich sagen, manuell bleiben |

**Die Regel gegen erfundene Wege:** Eine Stufe wird erst genannt, wenn ihr Auth-Weg belegt ist — Doku gelesen oder Endpunkt geprüft. Kein „es gibt bestimmt einen MCP-Server".

Am 21.07.2026 ist genau das schiefgegangen: Für HubSpot sah der HTTP-Endpunkt nach einer fertigen Anbindung aus, hatte aber kein `registration_endpoint`. Der echte Weg war das npm-Paket mit einem Private-App-Token. Wer die Stufe behauptet hätte, hätte den Nutzer in eine Sackgasse geschickt.

Belegte Beispiele als Muster, wie unterschiedlich Stufe 2 aussehen kann:

- **ClickUp** — offizieller MCP-Server, dokumentiert unter `developer.clickup.com/docs/connect-an-ai-assistant-to-clickups-mcp-server` (Stand 22.07.2026)
- **GoHighLevel** — LeadConnector MCP unter `services.leadconnectorhq.com/mcp/`, Bearer-PIT-Token plus `locationId`, 36 Tools (Stand 22.07.2026)

Diese beiden sind **Beispiele, keine Vorgaben.** Sie stehen hier, weil sie zeigen, dass „hat MCP" nichts über den Auth-Weg sagt.

### 3. Ruf in dieser Branche

Was Nutzer wirklich sagen, Vor- **und** Nachteile, aus Bewertungsquellen (G2, Capterra, Reddit, Trustpilot) — **nie aus Herstellertexten**. Ein Herstellertext beschreibt, was das Werkzeug können soll; die Bewertung beschreibt, was es tut.

### 4. Preis

Was gezahlt wird gegen das, was der Markt nimmt. Pro Platz, und was erst später dazukommt (Zusatzmodule, Volumengrenzen, Onboarding-Gebühren).

### 5. Urteil — genau drei Ausgänge

- **Behalten** — deckt die Aufgabe, Anbindung steht oder ist erreichbar
- **Behalten und die eine Lücke schließen** — Add-on, Integration oder ein Prozess drumherum
- **Wechsel wäre einen Blick wert** — nur wenn ein genannter Painpoint das trägt

## Das Bündel im Ganzen

Nach den Einzel-Dossiers ein Urteil über den ganzen Werkzeugkasten. Das sieht niemand, der nur Tool für Tool schaut:

| Frage | Woran erkennbar | Warum sie zählt |
|---|---|---|
| **Doppelt besetzt?** | Zwei Werkzeuge mit demselben „wofür" | Doppelte Kosten, geteilte Wahrheit, niemand weiß welches gilt |
| **Flickenteppich?** | Wo werden Daten von Hand von A nach B kopiert? Fällt aus den „wofür"-Antworten und den Painpoints | Jede Handkopie ist eine wiederkehrende Fehlerquelle und ein Automatisierungs-Kandidat |
| **Überdimensioniert?** | Werkzeugklasse gegen Betriebsgröße | Über- und Unterdimensionierung kosten beide, nur unterschiedlich |
| **Steuerbar?** | Anteil der Werkzeuge mit belegtem Anbindungsweg | **Die Kennzahl des Bündels:** „6 von 9 Werkzeugen kann Claude erreichen." Sagt in einer Zeile, wie weit Automatisierung überhaupt tragen kann |
| **Was kostet das zusammen?** | Summe der Abos gegen Betriebsgröße, plus was doppelt bezahlt wird | Oft der einzige Befund, der sofort Geld freisetzt |

Auch hier kein Alleinurteil: Doppelbesetzung kann bewusst sein, Überdimensionierung kann Wachstumsvorbereitung sein. Der Befund benennt die Beobachtung und die Frage dazu, nicht das Verdikt.

## Ablage

Ergebnisse nach `context/tool-dossiers.md`, je Werkzeug ein Block mit **Datum und Quelle** pro Aussage. Beim nächsten Lauf wird von dort gelesen; nachrecherchiert wird nur, was älter als drei Monate ist oder wofür der Nutzer eine Änderung gemeldet hat.
