#!/usr/bin/env python3
"""Re-freeze examples/dashboard.html from the demo data, with the private parts removed.

The example dashboard is embedded in WHAT-WORKS-BASE.html so a reader can click
through the real thing instead of looking at a screenshot. It is a snapshot, so it
goes stale in silence every time the template or the renderer moves on. check_repo.py
notices that; this script fixes it.

**Why this is a script and not a `cp`.** A plain copy carries the Tooling tab, and
that tab is read off the machine it was rendered on: installed CLIs, connected MCP
servers, plugins, keys. The first hand-made copy shipped 37 entries from a private
machine, one of them a client's name. So the copy happens here, with the scrub and
the checks attached to it.

    python3 reference/scripts/freeze_example.py
    python3 reference/scripts/freeze_example.py --check   # say what would change

Run it whenever check_repo.py reports the frozen example as older than the renderer.
"""
import html as html_mod
import pathlib
import re
import subprocess
import sys

W = pathlib.Path(__file__).resolve().parents[2]
RENDERED = W / 'context/today.html'
FROZEN = W / 'examples/dashboard.html'
PAGE = W / 'WHAT-WORKS-BASE.html'
START = '<!-- DEMO-FRAME-START'
END = '<!-- DEMO-FRAME-END -->'

PLACEHOLDER = """
    <p class="hint">The Tooling tab reads this machine on every render, so it shows something
    different for everyone. There is nothing meaningful to freeze into an example, and the
    original was scrubbed because it listed the tools and connections of the machine this copy
    was taken from.</p>
  """


def scrub(html: str) -> str:
    """Replace the machine-specific pane, then verify nothing private survived."""
    m = re.search(r'(<div class="tabpane" id="pane-tooling"[^>]*>)(.*?)(</div><!-- /pane-tooling)',
                  html, re.S)
    if not m:
        raise SystemExit('ABORT: the tooling pane was not found, so nothing was scrubbed. '
                         'The template changed shape; fix this script before shipping the copy.')
    html = html[:m.start(2)] + PLACEHOLDER + html[m.end(2):]

    home = str(pathlib.Path.home())
    if home in html:
        raise SystemExit(f'ABORT: {home} still appears in the copy after scrubbing. '
                         'Something outside the tooling pane carries an absolute path.')
    return html


def embed(page_html: str, dashboard: str) -> str:
    """Put the dashboard inside WHAT-WORKS-BASE.html as an iframe srcdoc.

    Not `src="examples/dashboard.html"`: Chrome gives every file:// URL its own
    origin, so a local src can come up blank in a page someone opened by double
    click, while rendering fine in a headless check. srcdoc inherits the page's
    origin, so it always runs, and it keeps the dashboard's CSS in its own document
    instead of colliding with the page's.
    """
    s = page_html.index(START)
    e = page_html.index(END) + len(END)
    frame = ('<!-- DEMO-FRAME-START: filled by reference/scripts/freeze_example.py, '
             'do not hand-edit -->\n'
             '          <iframe class="demo-frame" title="Example dashboard, with made-up data" '
             f'srcdoc="{html_mod.escape(dashboard, quote=True)}"></iframe>\n'
             '          <!-- DEMO-FRAME-END -->')
    return page_html[:s] + frame + page_html[e:]


def main() -> int:
    check_only = '--check' in sys.argv

    r = subprocess.run([sys.executable, str(W / 'reference/scripts/render_dashboard.py')],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr.strip() or r.stdout.strip(), file=sys.stderr)
        raise SystemExit('ABORT: the render failed, so there is nothing to freeze.')

    fresh = scrub(RENDERED.read_text(encoding='utf-8'))
    old = FROZEN.read_text(encoding='utf-8') if FROZEN.is_file() else ''

    def sync_page(dashboard):
        if not PAGE.is_file():
            return
        page = PAGE.read_text(encoding='utf-8')
        if START not in page:
            raise SystemExit('ABORT: WHAT-WORKS-BASE.html has no DEMO-FRAME slot any more.')
        updated = embed(page, dashboard)
        if updated != page:
            PAGE.write_text(updated, encoding='utf-8')
            print(f'WHAT-WORKS-BASE.html: embedded dashboard refreshed '
                  f'({len(updated) // 1024} KB total).')

    if fresh == old:
        # Same bytes, older timestamp. check_repo.py compares mtimes, so without this
        # touch it would report a stale example forever and the warning would stop
        # meaning anything.
        if not check_only:
            FROZEN.touch()
            sync_page(fresh)
            print('examples/dashboard.html was already current; timestamp refreshed.')
        else:
            print('examples/dashboard.html is already current.')
        return 0
    if check_only:
        print(f'examples/dashboard.html would change '
              f'({len(old.splitlines())} lines -> {len(fresh.splitlines())}).')
        return 0

    FROZEN.write_text(fresh, encoding='utf-8')
    sync_page(fresh)
    print(f'examples/dashboard.html re-frozen, tooling pane scrubbed '
          f'({len(fresh) // 1024} KB).')
    return 0


if __name__ == '__main__':
    sys.exit(main())
