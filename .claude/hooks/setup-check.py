#!/usr/bin/env python3
"""Am Anfang jeder Sitzung: ist dieser Workspace fertig eingerichtet?

Warum als Hook und nicht als Regel: eine Regel muss jemand befolgen. Gemessen
in einem echten Workspace lief das Morgen-Ritual, das denselben Selbsttest enthaelt,
in 90 Tagen sechs Mal. Was beim Start passieren soll, muss beim Start passieren.

Der Hook meldet sich NUR, wenn etwas fehlt, und dann in einer Zeile je Punkt,
in Alltagssprache mit dem naechsten Schritt. Ist alles da, schweigt er --
sonst wird er nach drei Tagen ueberlesen.

Geprueft wird nur, was still ausfaellt und teuer ist:

    Einrichtung nie gelaufen      der Ordner ist eine unbenutzte Kopie
    Einrichtung abgebrochen       Name steht drin, aber Schritte fehlen
    keine Sicherung               stirbt die Platte, ist alles weg
    kein Postfach, kein Kalender  das Briefing bleibt eine Aufgabenliste
    Schluessel fehlt              ein Werkzeug ist da und kann nichts

Alles davon faellt lautlos aus. Ein fehlendes Feature meldet sich; ein nie
eingerichtetes nicht.
"""
import json
import os
import pathlib
import subprocess
import sys

W = pathlib.Path(os.environ.get('CLAUDE_PROJECT_DIR') or os.getcwd())


def config_text():
    try:
        return (W / 'context/config.yaml').read_text(encoding='utf-8')
    except OSError:
        return ''


def hat_remote():
    try:
        r = subprocess.run(['git', '-C', str(W), 'remote'],
                           capture_output=True, text=True, timeout=5)
        return bool(r.stdout.strip())
    except Exception:
        return False


def pruefe():
    """Liste von (was fehlt, was es kostet, naechster Schritt).

    Die Frage "ist die Einrichtung ueberhaupt gelaufen" beantwortet bereits
    check-setup.sh am selben Ereignis, seit 21.07.2026 erprobt und mit dem
    zuverlaessigeren Marker: der setup-Ordner archiviert sich am Ende selbst
    weg. Solange er da ist, schweigt dieser Hook -- sonst melden sich zwei
    Stimmen zum selben Thema, und der Nutzer hoert bei der zweiten weg.
    """
    if (W / '.claude/skills/setup').is_dir():
        return []

    offen = []
    cfg = config_text()
    if not cfg or '[YOUR NAME]' in cfg or '[DEIN NAME]' in cfg:
        return []                     # check-setup.sh hat das Wort

    if not hat_remote():
        offen.append(('Kein Sicherungs-Repo',
                      'stirbt die Platte, ist deine Arbeit weg',
                      'sag „richte mein Backup ein"'))

    # Ein Postfach-Slot gilt als belegt, sobald irgendein Weg dorthin steht --
    # Connector ODER CLI. Deshalb wird der Text gesucht, nicht eine Struktur.
    if 'slot: mail' not in cfg and 'gws' not in cfg:
        offen.append(('Kein Weg zu deinem Postfach',
                      'das Briefing bleibt eine Aufgabenliste statt deines Tages',
                      'sag „verbinde mein Postfach"'))
    if 'slot: calendar' not in cfg and 'slot: kalender' not in cfg:
        offen.append(('Kein Kalender verbunden',
                      'deine Termine tauchen im Briefing nicht auf',
                      'sag „verbinde meinen Kalender"'))

    # Ein Schluessel, den die Ausstattung behauptet, der aber nicht existiert:
    # das Werkzeug ist da und kann nichts, und niemand merkt es.
    keys = pathlib.Path.home() / '.config/credentials.env'
    txt = keys.read_text(encoding='utf-8', errors='ignore') if keys.is_file() else ''
    for name, zweck in (('FIRECRAWL_API_KEY', 'Webseiten lesen'),
                        ('OPENROUTER_API_KEY', 'Bilder und Spezialmodelle')):
        if name in cfg and name not in txt:
            offen.append((f'Der Schlüssel für {zweck} fehlt',
                          'das Werkzeug ist eingerichtet und kann nichts',
                          f'sag „trag meinen {name.split("_")[0].title()}-Schlüssel ein"'))
    return offen


def main():
    try:
        json.load(sys.stdin)
    except Exception:
        pass

    try:
        offen = pruefe()
    except Exception:
        return 0                      # ein Hinweis blockiert nie eine Sitzung

    if not offen:
        return 0                      # fertig eingerichtet: schweigen

    zeilen = '\n'.join(f'- **{was}** — {kostet}. {schritt}' for was, kostet, schritt in offen)
    text = (
        f"Beim Start geprueft: an diesem Workspace fehlen noch {len(offen)} Sachen.\n"
        f"{zeilen}\n"
        "Sag das dem Nutzer EINMAL, in seinen Worten, hoechstens zwei Saetze, nach "
        "deiner eigentlichen Antwort und nie davor. Kein zweites Mal in dieser "
        "Sitzung, und kein Draengen: er entscheidet, ob und wann."
    )
    print(json.dumps({'hookSpecificOutput': {
        'hookEventName': 'SessionStart',
        'additionalContext': text,
    }}))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
