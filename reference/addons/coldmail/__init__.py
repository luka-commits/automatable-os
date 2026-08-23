"""The cold mail add-on's dashboard tab.

Cold mail is not Upwork with different words. Upwork is pull acquisition — the jobs
already exist, you find them and apply — so its tab always shows the same thing: a
list of jobs with a status each. Cold mail is push. Nobody is looking for you, and
the work goes through **phases** that take weeks:

    week 1      mailboxes warming up. Nothing to do, and sending now would burn
                the domains. The one thing worth showing is how many days are left.
    week 1-3    the list gets built and the mails get written, in parallel.
    from then   replies arrive. That is the only daily action there is.

So this tab shows different things at different times, and that is deliberate. A
fixed dashboard would spend week one telling someone about 2,483 leads they must
not mail yet.

**What it deliberately does not show:** score distributions, coverage rates, factor
counts. Those are the machine's own metrics — useful while building the machine,
noise on a morning dashboard. The test for anything here is whether it changes what
the reader does today.

The names it needs from the base (W, esc, TXT, TODAY and so on) are injected into
this module's namespace by the loader before render() is called.

    render() -> str   the tab's HTML, or '' when the add-on has nothing to say yet
"""

import datetime
import re
import sqlite3

# The lead store. It does not exist until the pipeline has run once, and that is a
# normal state rather than an error: setup comes first, leads come later.
DB = 'context/.coldmail.db'

# Instantly asks for two weeks minimum before a campaign and recommends four. We
# count against 14 because that is the number a user may act on; the tab says the
# longer one is better rather than blocking them at 28.
WARMUP_DAYS = 14

CM_I18N = {
    'en': {
        'warmup_head': 'Mailboxes warming up',
        'warmup_body': 'Day {done} of {total}. Sending before they are warm lands in spam, '
                       'and the reputation that costs is not repaired by waiting afterwards.',
        'warmup_done': 'Warmup finished',
        'warmup_ready': '{n} mailboxes ready, {cap} mails a day.',
        'no_setup': 'Not set up yet.',
        'no_setup_hint': 'Say <code>set up cold mail</code> to work out how many mailboxes '
                         'and domains your target needs, and what it costs.',
        'leads_head': 'The list',
        'leads_none': 'No leads yet. Say <code>coldmail-run</code> to pick a niche and build one.',
        'leads_body': '{ready} ready to send out of {total} scraped.',
        'leads_pending': '{n} still need an address.',
        'replies_head': 'Replies',
        'replies_none': 'No replies waiting.',
        'replies_body': '{n} waiting for an answer.',
        'sent_body': '{n} sent so far.',
    },
    'de': {
        'warmup_head': 'Postfächer wärmen auf',
        'warmup_body': 'Tag {done} von {total}. Wer vorher sendet, landet im Spam, und der '
                       'Ruf, den das kostet, kommt durch Warten danach nicht zurück.',
        'warmup_done': 'Aufwärmen fertig',
        'warmup_ready': '{n} Postfächer bereit, {cap} Mails am Tag.',
        'no_setup': 'Noch nicht eingerichtet.',
        'no_setup_hint': 'Sag <code>richte cold mail ein</code> — dann rechnen wir aus, wie viele '
                         'Postfächer und Domains dein Ziel braucht und was es kostet.',
        'leads_head': 'Die Liste',
        'leads_none': 'Noch keine Leads. Sag <code>coldmail-run</code>, um eine Nische zu wählen.',
        'leads_body': '{ready} versandfertig von {total} gescrapten.',
        'leads_pending': '{n} fehlt noch eine Adresse.',
        'replies_head': 'Antworten',
        'replies_none': 'Keine Antworten offen.',
        'replies_body': '{n} warten auf eine Antwort.',
        'sent_body': '{n} verschickt.',
    },
}


def _t():
    return CM_I18N.get(LANG, CM_I18N['en'])            # noqa: F821 — injected


def _cfg(key):
    """One value out of config.yaml, without a YAML parser.

    The base reads the same file as text elsewhere (`<name>_enabled: false`), and a
    dependency for four scalars would be the wrong trade. Anything more structured
    than this belongs in the database, not in config.
    """
    try:
        text = CONFIG.read_text(encoding='utf-8')      # noqa: F821 — injected
    except Exception:
        return None
    m = re.search(rf'^{re.escape(key)}:\s*(.+?)\s*(?:#.*)?$', text, re.M)
    if not m:
        return None
    v = m.group(1).strip().strip('"\'')
    return v or None


def _int(key):
    v = _cfg(key)
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _zahlen():
    """What the lead store knows. Empty dict when it is not there yet.

    Never invents a zero: a missing database means "we have not started", not "we
    have nothing", and those two read very differently on a dashboard.
    """
    p = W / DB                                          # noqa: F821 — injected
    if not p.is_file():
        return {}
    try:
        con = sqlite3.connect(f'file:{p}?mode=ro', uri=True, timeout=2)
        try:
            have = {r[0] for r in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
            out = {}
            if 'leads' in have:
                row = con.execute(
                    'SELECT count(*), '
                    "sum(case when status='ready' then 1 else 0 end), "
                    "sum(case when status='needs_email' then 1 else 0 end), "
                    "sum(case when status='sent' then 1 else 0 end) FROM leads").fetchone()
                out.update(total=row[0] or 0, ready=row[1] or 0,
                           pending=row[2] or 0, sent=row[3] or 0)
            if 'replies' in have:
                out['replies'] = con.execute(
                    'SELECT count(*) FROM replies WHERE answered_at IS NULL').fetchone()[0]
            return out
        finally:
            con.close()
    except sqlite3.Error:
        # A locked or half-written database is not worth taking the render down for.
        return {}


def _karte(kopf, text, ton='', extra=''):
    klasse = f'cm-card{" cm-" + ton if ton else ""}'
    return (f'    <div class="{klasse}">\n'
            f'      <h3>{esc(kopf)}</h3>\n'                       # noqa: F821 — injected
            f'      <p>{text}</p>\n{extra}'
            f'    </div>')


def _aufwaermen(t):
    """The one thing that matters in week one: may I send yet?"""
    start = _cfg('coldmail_warmup_started')
    boxen = _int('coldmail_mailboxes')
    if not start:
        return None
    try:
        d0 = datetime.date.fromisoformat(start)
    except ValueError:
        return None
    tage = (TODAY - d0).days                                       # noqa: F821 — injected
    if tage < WARMUP_DAYS:
        anteil = max(0, min(100, round(100 * tage / WARMUP_DAYS)))
        balken = (f'      <div class="cm-bar"><span style="width:{anteil}%"></span></div>\n')
        return _karte(t['warmup_head'],
                      esc(t['warmup_body'].format(done=max(tage, 0), total=WARMUP_DAYS)),  # noqa: F821
                      'warn', balken)
    if boxen:
        return _karte(t['warmup_done'],
                      esc(t['warmup_ready'].format(n=boxen, cap=boxen * 30)),  # noqa: F821
                      'ok')
    return None


def render():
    """The tab, or '' when the add-on is switched on but nothing has happened yet.

    Returning '' is what makes the tab disappear entirely — the base treats an empty
    body as "not installed". That is the right answer for a user who enabled the
    add-on and has not run setup: a tab that only says "nothing here" is worse than
    no tab, because they have to click it to find that out.
    """
    t = _t()
    z = _zahlen()
    hat_setup = bool(_cfg('coldmail_warmup_started') or _int('coldmail_mailboxes'))
    if not hat_setup and not z:
        return ''

    karten = []

    if not hat_setup:
        karten.append(_karte(t['no_setup'], t['no_setup_hint']))
    else:
        k = _aufwaermen(t)
        if k:
            karten.append(k)

    # Replies first once there are any — it is the only line here that asks for
    # something to be done today.
    offen = z.get('replies')
    if offen:
        karten.insert(0, _karte(t['replies_head'],
                                esc(t['replies_body'].format(n=offen)), 'ok'))  # noqa: F821

    if z:
        zeilen = [esc(t['leads_body'].format(ready=z.get('ready', 0),  # noqa: F821
                                             total=z.get('total', 0)))]
        if z.get('pending'):
            zeilen.append(esc(t['leads_pending'].format(n=z['pending'])))  # noqa: F821
        if z.get('sent'):
            zeilen.append(esc(t['sent_body'].format(n=z['sent'])))  # noqa: F821
        karten.append(_karte(t['leads_head'], ' '.join(zeilen)))
    elif hat_setup:
        karten.append(_karte(t['leads_head'], t['leads_none']))

    return '  <div class="cm-grid">\n' + '\n'.join(karten) + '\n  </div>'
