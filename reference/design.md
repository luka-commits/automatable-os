# Design system

The colours, spacings and patterns the dashboard is built from. Two reasons why this is here:

1. **If you build your own tools**, you can style them with these values. Then they look like part of the same system and not like five different programs.
2. **If Claude designs something for you**, you just say "stick to `reference/design.md`" and get a consistent result instead of a new look on every attempt.

All values are defined in the dashboard as CSS variables (`context/today_template.html`, right at the top). Change them there and the whole dashboard changes with them. `SYSTEM.html` carries the same block, and so does the pitch-page template.

## Attitude

Warm paper rather than cool white, one accent colour, serif for anything that announces itself. **This is the same palette the pitch pages use**, deliberately: what a client opens and what you work in every morning should be recognisably one thing.

Colour always means something here. The accent marks what is active or done; amber and red are warning levels. Everything else is neutral. Using colour as decoration takes its meaning away.

## Colours

Every ratio below was measured, not estimated, and it sits next to the token so it survives the next person who finds a lighter shade prettier.

**Surfaces**

| Token | Value | What for |
|---|---|---|
| `--bg` | `#f3efe6` | Page background. Warm paper, not a cool near-white |
| `--bg-band` | `#ece5d7` | A shade down: header, table heads, code chips |
| `--card` | `#fbf9f4` | Cards and panels |
| `--ink` | `#1c1712` | Warm near-black, for an inverted band |
| `--on-ink` | `#f3efe6` | Text on `--ink`, 15.5:1 |
| `--border` / `--border-strong` / `--border-soft` | `#e2d9c8` · `#cfc2ab` · `#eae3d3` | Normal edge · when it has to be distinct · barely there |

**Text**

| Token | Value | On `--bg` | What for |
|---|---|---|---|
| `--text` | `#262019` | 14.0:1 | Headings, important values |
| `--text-2` | `#5c5347` | 6.6:1 | Body text |
| `--text-3` | `#6f6656` | 4.9:1 (5.4:1 on `--card`) | Labels, secondary information |

**The accent, and why there are two of it**

| Token | Value | On `--bg` | What for |
|---|---|---|---|
| `--accent` | `#c1663e` | 3.5:1 | Large text, borders, dots, fills. **Never small text** |
| `--accent-deep` | `#a24f2e` | 5.0:1 | Anything small, and what white sits on |
| `--accent-soft` | `#f3e4db` | | Surfaces with an accent backing |

3.5:1 clears the bar for large text and for things that are not text at all. It does not clear it for a 12px label, which is why `--accent-deep` exists. Reaching for `--accent` on small text is the one mistake this pair is here to prevent.

**Warning levels**

| Token | Value | What for |
|---|---|---|
| `--sev-amber` / `--amber-soft` / `--amber-border` | `#B54708` · `#f7ecd9` · `#e3caa0` | Attention, but not urgent |
| `--sev-red` / `--red-soft` / `--red-border` | `#B42318` · `#FBE8E5` · `#F5C5BE` | Overdue, failed, blocked |

There are no more colours than these. If you need another meaning, first check whether one of the existing ones already carries it.

**The old names still resolve.** `--brand`, `--brand-deep` and `--brand-soft` alias to the accent trio, because a dozen places refer to them and renaming would be churn with no reader on the other end.

## Type

**Serif for display, sans for everything else.** `Georgia, "Iowan Old Style", "Times New Roman", ui-serif, serif` carries the page title, section headings, the briefing lead, and any number meant to be read as a figure rather than a count.

Always at **weight 400**, with tight letter-spacing (-.015em to -.024em). A bold serif reads as shouting, and at display size the size is already doing the work.

Everything else is the system sans: body at 14px/1.55, labels at 11.5 to 12.5px.

Both are system fonts, deliberately not loaded from anywhere.

## Spacing, corners, shadows

| Token | Value | What for |
|---|---|---|
| `--gap` | `14px` | Spacing between cards |
| `--shadow-1` | `0 1px 2px rgba(28,23,18,.05)` | Resting surfaces |
| `--shadow-2` | `0 6px 20px rgba(28,23,18,.09)` | Highlighted surfaces |
| `--ease` | `cubic-bezier(.16,1,.3,1)` | Every movement, so nothing feels hectic |

**Radii:** `999px` for chips and pills, `16px` for large panels, `14px` for cards, `8px` for small surfaces like code chips. No more steps than that are needed.

## Patterns

**Card:** `--card` surface, `--border`, `--shadow-1`, generous inner padding. Heading in `--text`, content in `--text-2`, labels small in `--text-3`.

**Status at a glance:** a coloured dot, a coloured number or a coloured edge, never a coloured block. Set up is the accent, not set up is grey, not red. Red is reserved for broken, never for unfinished.

Learned by getting it wrong: `.ok` was set on the container of a row, which tinted the label and the subtitle along with the count and made half the tooling list read as links. State belongs on the one element that carries it.

**Technical values** (commands, paths, keys) always in monospace on their own calm surface. The reader should see immediately what they can copy.

**Empty areas** get a calm sentence about what will appear there and how to fill it. Never an empty field, and never an error message when there is simply nothing there yet. A freshly set-up system must not look like a broken one.

## Limits

The dashboard is a single HTML file that works on a double click. Therefore: **no external fonts, no icon libraries, no CDN, no build step.** Icons are embedded SVG (the sprite sheet sits at the top of `today_template.html`), fonts are system fonts. Building in an external dependency makes the file useless offline.
