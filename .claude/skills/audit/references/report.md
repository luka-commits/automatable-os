# Berichtsform

Gelesen in Schritt 3 und 4 von `/audit`. Regelt, wie Befunde und Vorschläge formuliert werden.

## Der Bericht im Chat

Aufbau, in dieser Reihenfolge:

1. **Ein Satz Gesamturteil.** Nicht „das Audit ist abgeschlossen", sondern was Sache ist: „Der Ordner trägt, aber die Hälfte deiner Dokumente ist für Claude unsichtbar."
2. **Je Dimension höchstens eine Zeile**, und nur für die, die etwas zu sagen haben. Dimensionen auf `ok` werden in einem Sammelsatz erledigt („Sicherung, Kaltstart und Entscheidungs-Gedächtnis sind in Ordnung"). Niemand liest eine Liste bestandener Prüfungen.
3. **Die drei Dinge mit dem größten Hebel**, ausformuliert. Warum drei: mehr wird nicht umgesetzt, weniger wirkt beliebig.
4. **Was `unknown` blieb**, in einem Halbsatz, mit dem Grund. Ein fehlender Beleg ist keine gute Note.

## Wie ein Befund formuliert wird

**Konsequenz statt Messwert.** Der Messwert ist die Herkunft der Aussage, nicht die Aussage.

| Nicht so | Sondern so |
|---|---|
| „12 Waisen-Dokumente gefunden" | „Diese zwölf Dokumente liest Claude nie, weil nichts auf sie zeigt" |
| „Token-Last 18.400" | „Jede Unterhaltung zahlt rund 18.000 Token, bevor irgendetwas passiert" |
| „5 Wiederholungsmuster erkannt" | „Diesen Ablauf hast du 40-mal von Hand getippt" |
| „confidence 0.9, severity high" | (Werte gehören in die JSON, nicht in den Satz) |

Jeder Befund beantwortet drei Dinge: **was ist**, **warum das schadet**, **was dagegen hilft**. Fehlt der mittlere Teil, ist es eine Statistik und keine Erkenntnis.

**Keine Schulnoten, keine Prozentwerte über alles.** Ein Gesamtscore mittelt einen toten Journal-Strang gegen sauberes Repo-Handling weg und suggeriert Vergleichbarkeit, die es nicht gibt.

## Wie Vorschläge aussehen

**Nie eine Einzelempfehlung.** Es gibt kein bestes Werkzeug und keinen besten Weg, es gibt Abwägungen — und wer nur einen Weg nennt, nimmt dem Gegenüber die Entscheidung ab, die ihm gehört.

Je Vorschlag zwei bis drei Wege nebeneinander, in einer Tabelle:

| Weg | Aufwand | Laufend | Was du dafür bekommst | Was du dir einhandelst |
|---|---|---|---|---|
| … | einmalig 20 min | 0 € | … | … |

Darunter **eine** markierte Empfehlung mit Begründung in einem Satz („würde ich nehmen, weil …"). Die anderen Wege bleiben gleichwertig stehen, jeder mit seinem eigenen Vorteil — sie sind keine Strohmänner.

**Was jemand schon benutzt, schlägt das theoretisch bessere Werkzeug.** Ein Wechsel taucht nur als Option auf, wenn ein genannter Painpoint ihn trägt. Einem Betrieb den Umstieg zu empfehlen, weil etwas „Best Practice" ist, ist schlechte Beratung: der Umstieg kostet Wochen, und der Schmerz war ein anderer.

## Ton

Ein erfahrener Mensch, der sich das Setup angesehen hat und jetzt sagt, was ihm aufgefallen ist. Nicht „Diagnose abgeschlossen, 7 von 11 Prüfungen bestanden".

- Alltagssprache. Fachbegriffe nur, wo sie etwas hinzufügen.
- Keine Dringlichkeits-Rhetorik. Kein „kritisch", kein „dringend", keine Ausrufezeichen. Was wirklich wehtut, erkennt man an der beschriebenen Konsequenz.
- Offene Punkte sind Möglichkeiten, keine Vorwürfe. Ein Ordner ohne Routinen ist nicht nachlässig geführt, er hat eine Möglichkeit noch nicht genutzt.
- Keine Em-Dashes.
