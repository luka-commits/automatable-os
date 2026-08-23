#!/usr/bin/env python3
"""casualize.py — the ONE shared home for the cold-email var-prep helpers.

Lifted verbatim from the battle-tested v5 pipeline (assemble_v5.py `name_from_email`/`display_name`,
with Luka's 2026-06-07/08 fixes) into a side-effect-free module so build_vars + any future variant
import the SAME proven logic instead of re-inventing weak regex. (We can't import assemble_v5/
seo_enrich_run directly — they touch DataForSEO env vars at module load and crash on import.)

What's here:
  name_from_email(email, business_name)  -> owner first name from the prefix, or '' (rejects roles
                                            info@/sales@, initials jb@, and the brand-as-prefix case)
  display_name(bn, niche, city='')        -> casualise a business name to a short brand ('' if generic)
                                            — used for BOTH the lead's company AND competitor names
  greeting(first, company_casual)          -> first name if found, ELSE casualised company (Luka's rule)
  location(town, region)                   -> town, or region as the fallback when the scrape was city-less
"""
import re

# generic tokens dropped when casualising a brand for the greeting, per niche
NICHE_GENERIC = {
    'gyms': {'gym', 'gyms', 'fitness', 'studio', 'studios', 'centre', 'center', 'club', 'health',
             'training', 'personal', 'wellness', 'the', 'and', '&', 'of', 'in', 'co', 'ltd',
             'limited', 'llp', 'uk', 'hk', 'co.'},
    'cleaning': {'cleaning', 'cleaners', 'cleaner', 'clean', 'services', 'service', 'commercial',
                 'office', 'domestic', 'company', 'ltd', 'limited', 'the', 'in', 'of', 'co', 'group'},
    'locksmith': {'locksmith', 'locksmiths', 'locksmithing', 'security', 'secure', 'locks', 'lock',
                  'key', 'keys', 'auto', 'car', 'vehicle', 'emergency', 'hour', 'hours', '24hr', '24/7',
                  'mobile', 'services', 'service', 'solutions', 'systems', 'safe', 'safes', 'engineers',
                  'engineer', 'and', '&', 'the', 'of', 'in', 'co', 'co.', 'ltd', 'limited', 'llp',
                  'uk', 'company', 'group', 'centre', 'center'},
}
ROLE = {'info', 'contact', 'hello', 'enquiries', 'enquiry', 'admin', 'sales', 'office', 'bookings',
        'booking', 'mail', 'team', 'hi', 'accounts', 'support', 'help', 'reception', 'members'}
NAME_STOP = ROLE | {'service', 'services', 'quote', 'quotes', 'jobs', 'careers', 'marketing', 'noreply',
                    'no-reply', 'email', 'mailbox', 'general', 'manager', 'owner', 'customerservice',
                    'clean', 'cleaning', 'pest', 'pools', 'pool', 'electrical', 'plumbing', 'fitness',
                    'locksmith', 'locksmiths', 'locks', 'security', 'welcome', 'enquire', 'newbusiness',
                    'hellothere', 'getintouch', 'callus'}
GEO_STRIP = {'hk', 'uk', 'u.k', 'au', 'aus', 'usa', 'u.s', 'us', 'nz', 'sg', 'uae', 'ie',
             'hong', 'kong', 'australia', 'singapore', 'ireland', 'sydney', 'melbourne',
             'brisbane', 'perth', 'adelaide', 'canberra', 'london', 'dublin'}
FILLER_STRIP = {'guy', 'guys', 'man', 'men', 'pro', 'pros', 'crew', 'expert', 'experts',
                'people', 'team', 'co'}


def name_from_email(email, business_name=''):
    """Owner first name from the email prefix WHEN it's clearly a personal name (jason@, paula.s@)
    — NOT a role (info@/sales@), initials (jb@), or the brand itself (sparkcleaning@sparkcleaning.com)."""
    email = (email or '')
    if '@' not in email:
        return ''
    local, dom = email.split('@', 1)
    dom = dom.split('.')[0].lower()
    tok = re.sub(r'\d+', '', re.split(r'[._\-]', local.lower())[0])   # firstname.lastname -> firstname
    if not tok.isalpha() or not (3 <= len(tok) <= 11):                # initials / merged-brand / empty
        return ''
    if tok in NAME_STOP:
        return ''
    bn = re.sub(r'\W', '', (business_name or '').lower())
    if tok in dom or dom in tok or (bn and (tok in bn)):             # prefix == the brand, not a person
        return ''
    return tok.title()


def _tc(n):
    """Title-case but keep acronyms (AC, REMS), stylised caps (LockFit), and ordinals (1st, not '1St')."""
    out = []
    for w in n.split():
        if re.match(r'^\d+(st|nd|rd|th)$', w.lower()):
            out.append(w.lower())
        elif w.isupper() and len(w) <= 4:
            out.append(w)
        elif any(c.isupper() for c in w):
            out.append(w)
        else:
            out.append(w.title())
    return ' '.join(out)


def clean_name(name, town=''):
    """CONSERVATIVE clean for a name that must stay RECOGNISABLE — the lead's company_casual and the
    competitor names. Only drops a ' - City'/' | x' tail, legal suffixes, a leading 'The', and a
    trailing bare town token (when brand words remain). KEEPS the brand (Locksmiths/Lock/Key stay).
    NEVER returns empty — falls back to the trimmed raw name. This is NOT the aggressive stem."""
    n = re.split(r'\s+[-–]\s+|[,|/()]', (name or '').strip())[0].strip()
    n = re.sub(r'\s+(ltd|limited|llp|plc|inc|co)\.?$', '', n, flags=re.I).strip()
    words = [w for w in n.split() if w]
    if len(words) > 1 and words[0].lower() == 'the':
        words = words[1:]
    if town and len(words) > 1 and words[-1].strip('.,&').lower() == town.strip().lower():
        words = words[:-1]
    n = ' '.join(words).strip(' .,&-')
    return _tc(n) or (name or '').strip()


def display_name(bn, niche, city='', hood=''):
    """AGGRESSIVE brand stem for the GREETING fallback only ('Hey {stem},'). Strips generic/city/geo
    words to a short stem. Returns '' if it collapses to a city/fragment/generic — caller then uses
    'there'. Do NOT use for company_casual or competitors (use clean_name — this over-strips).

    `hood` ist der Stadtteil aus `raw.neighborhood` (23.08.2026). Ohne ihn blieb "CitySentry
    Locksmith Pimlico" vollstaendig stehen: die Schleife trimmt von hinten und bricht beim
    ersten unbekannten Wort ab, und Pimlico ist kein `town` -- London ist es. Die Anrede
    lautete damit "hey citysentry locksmith pimlico", also der volle Firmeneintrag an einen
    Fremden. Das Feld liegt im Scrape und kostet nichts.
    """
    gen = set(NICHE_GENERIC.get(niche, set())) | GEO_STRIP | FILLER_STRIP
    for ort in (city, hood):
        if ort:
            gen |= {w for w in ort.lower().split() if w}
    n = re.split(r'[,|/()]| - ', (bn or '').strip())[0].strip()
    words = [w for w in n.split() if w]
    if len(words) > 1 and words[0].lower() == 'the':
        words = words[1:]
    # ERST die generischen Woerter UEBERALL raus, dann von hinten trimmen (23.08.2026).
    # Vorher lief nur die Trimm-Schleife, und die haelt beim ersten unbekannten Wort an --
    # "CitySentry Locksmith Pimlico" behielt deshalb sein "Locksmith" mitten drin, obwohl
    # genau dieses Wort die Liste kennt. Ein Nischenwort in der Mitte ist derselbe Ballast
    # wie eins am Ende.
    # ABER NIE DAS ERSTE WORT: der Markenkern beginnt fast immer vorne, und dort steht das
    # Nischenwort nicht zufaellig. "Key Moment Security" wurde beim ersten Versuch zu
    # "moment" -- "key" ist bei Schluesseldiensten generisch und hier trotzdem der Name.
    # Dasselbe traefe "Lock Solutions" und "Auto Locks".
    nische = set(NICHE_GENERIC.get(niche, set()))
    if len(words) > 1:
        words = words[:1] + [w for w in words[1:] if w.strip('.&,').lower() not in nische]
    while words and words[-1].strip('.&,').lower() in gen:
        words.pop()
    n = ' '.join(words[:3]).strip(' .,&-')
    n = re.sub(r'\s+(ltd|limited|llp)\.?$', '', n, flags=re.I).strip()
    toks = [t for t in re.split(r'\W+', n.lower()) if t]
    if not toks or all(t in gen for t in toks):
        return ''
    if len(toks) == 1 and (toks[0] in {'all', 'the', 'a', 'an', 'your', 'our', 'us', 'we', 'best', 'top', 'my',
                                       'mr', 'mrs', 'ms', 'dr', 'miss', 'mr.', 'no', 'sure'}
                           or toks[0] in GEO_STRIP or toks[0].isdigit()):  # lone city/number/title/weak ≠ brand
        return ''
    return _tc(n)


# Woerter, auf denen ein Markenkern nicht enden darf. "Auto Keys Of Bedford" wurde zu
# "Auto Keys Of" und daraus die Anrede "hey Auto Keys Of," -- ein abgeschnittener Satz.
_DANGLING = {'of', 'and', 'the', 'for', 'in', 'at', 'to', 'by', 'on', 'with', 'from',
             '&', 'a', 'an', 'or', 'de', 'von', 'der', 'die', 'das', 'und'}


def _trim_dangling(stem):
    """Haengende Fuellwoerter am Ende abschneiden, sonst bleibt ein halber Name stehen."""
    words = (stem or '').split()
    while words and words[-1].strip('.,&').lower() in _DANGLING:
        words.pop()
    return ' '.join(words)


def is_town_fragment(stem, town):
    """Ist der Markenkern nur ein Stueck des Ortsnamens?

    display_name streicht generische Woerter von hinten und prueft am Ende, ob ALLE
    Tokens generisch sind. Bei mehrwortigen Orten greift das nicht: "King's Lynn Car
    keys" wurde zu "King's Lynn" -- die Anrede waere der Ort gewesen, nicht die Firma.

    Erster Loesungsversuch legte die Ortsbestandteile in die Streichliste. Das war
    schlimmer: der Stripper frass sie einzeln und liess Fragmente stehen ("Hey King's,",
    "Hey Bury St,"). Deshalb hier als NACHpruefung: wenn jedes Wort des Stamms im
    Ortsnamen vorkommt, ist es kein Markenkern.
    """
    if not stem or not town:
        return False
    # Beide Seiten durch dieselbe Normalisierung, sonst scheitert der Vergleich an der
    # Abkuerzung: die Firma schreibt "Bury St Edmunds", Google fuehrt "Bury SAINT Edmunds".
    _norm = lambda s: {w for w in re.split(r"[\s,'’./-]+", casual_town(s).lower()) if w}
    tw = _norm(town)
    st = [w for w in re.split(r"[\s,'’./-]+", casual_town(stem).lower()) if w]
    return bool(st) and all(w in tw for w in st)


def casual_brand(name, niche, town='', hood=''):
    """The MOST casual usable brand for the greeting: the aggressive stem ('JJ Locksmiths'->'JJ',
    '1st Defence Locksmiths Leeds'->'1st Defence', 'Lockforce Locksmith Leeds'->'Lockforce') when it
    yields a real brand — else fall back to the recognisable clean_name so it never collapses to a
    city/fragment/empty ('Leeds Locksmith' stays 'Leeds Locksmith', not 'Leeds')."""
    stem = _trim_dangling(display_name(name, niche, town, hood))
    if stem and is_town_fragment(stem, town):
        stem = ''                      # lieber der volle Name als der Ort in der Anrede
    if stem:
        return stem
    # Auch der Rueckfall kann auf den Ort zusammenfallen: "Bury St Edmunds Locks" wird von
    # clean_name zu "Bury St Edmunds". Dann lieber gar keine Marke -- greeting() setzt
    # "there" ein, und das ist besser als jemanden mit seinem Ortsnamen anzureden.
    # Auch der Rueckfall muss getrimmt werden: display_name gab bei "Auto Keys Of Bedford"
    # nichts zurueck, clean_name lieferte "Auto Keys Of", und daraus wurde die Anrede
    # "hey Auto Keys Of," -- ein abgeschnittener Satz an einen Fremden.
    fallback = _trim_dangling(clean_name(name, town))
    return '' if is_town_fragment(fallback, town) else fallback


def greeting(first, company_casual):
    """Luka's rule: the first name if we found one, else the casualised company, else a neutral fallback."""
    return first or company_casual or 'there'


def casual_town(town):
    """Der Ortsname so, wie ein Einheimischer ihn schreibt.

    Google fuehrt die kanonische Langform: "Bury Saint Edmunds", "Saint Helens",
    "Saint Leonards-on-sea", "Ipswich, Suffolk". In einer Mail liest sich das wie ein
    Datenbank-Export. Gemessen an der Locksmith-Liste: 50 von 5.409 Places tragen ein
    ausgeschriebenes "Saint", dazu uneinheitliche Gross-Kleinschreibung in den
    Bindestrich-Namen.

    Bewusst konservativ: nur belegte Muster, nichts geraten. Ein falsch "verschoenerter"
    Ortsname ist schlimmer als ein steifer, weil der Empfaenger sofort sieht, dass wir
    an seinem Ort herumgebastelt haben.
    """
    t = (town or '').strip()
    if not t:
        return ''
    t = t.split(',')[0].strip()                       # "Ipswich, Suffolk" -> "Ipswich"
    t = re.sub(r'\bSaint\b', 'St', t, flags=re.I)     # niemand sagt "Saint Helens"
    # KEINE Gross-Kleinschreibung anfassen. Ein erster Versuch tat das mit einer Liste
    # bekannter Verbinder und zerstoerte prompt drei echte Orte: Ashby-de-la-Zouch wurde
    # zu "de-La", Grange-over-Sands zu "Over", Newbiggin-by-the-Sea zu "By". Jede solche
    # Liste ist unvollstaendig, und ein verhunzter Ortsname faellt dem Empfaenger sofort
    # auf. "St Leonards-on-sea" bleibt also mit kleinem "sea" -- steif, aber richtig.
    return t


def location(town, region):
    """City for the copy; fall back to the region when the scrape came back city-less (~10-33% do)."""
    return casual_town(town) or casual_town(region)
