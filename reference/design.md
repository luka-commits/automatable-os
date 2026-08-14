# Design system

The colors, spacings and patterns the dashboard is built from. Two reasons why this is here:

1. **If you build your own tools**, you can style them with these values. Then they look like part of the same system and not like five different programs.
2. **If Claude designs something for you**, you just say "stick to `reference/design.md`" and get a consistent result instead of a new look on every attempt.

All values are defined in the dashboard as CSS variables (`context/today_template.html`, right at the top). Change them there and the whole dashboard changes with them.

## Attitude

Calm, matter-of-fact, little color. Color always means something here: green is the system itself, amber and red are warning levels. Everything else is neutral. Whoever uses color as decoration takes away its meaning.

## Colors

**Accent (the system itself)**

| Token | Value | What for |
|---|---|---|
| `--brand` | `#177B57` | Active elements, accent lines, the current tab |
| `--brand-deep` | `#0B3F2D` | Text on light green surfaces |
| `--brand-soft` | `#E8F1ED` | Surfaces with a green backing |

**Surfaces and text**

| Token | Value | What for |
|---|---|---|
| `--bg` | `#F7F8F7` | Page background, slightly warm instead of pure white |
| `--card` | `#FFFFFF` | Cards and panels |
| `--text` | `#0D1F1A` | Headings, important values |
| `--text-2` | `#3F4D47` | Body text |
| `--text-3` | `#68736D` | Labels, secondary information |
| `--border` | `#E2E6E3` | Normal dividing lines |
| `--border-strong` | `#C8CFCB` | When an edge has to be more distinct |

**`--text-3` has a floor, and it is not a matter of taste.** It was `#7A857F` and got darkened, because measured against `--bg` that gave 3.59:1 and against `--card` 3.83:1 — below the 4.5:1 that normal-sized text needs to stay readable. Labels are small text, so they need the full ratio, not the 3:1 that large text gets away with. If you lighten it again because it looks more elegant, you are trading legibility for elegance on exactly the text people squint at. Current values: **4.63:1** on the background, **4.93:1** on cards.

**Warning levels**

| Token | Value | What for |
|---|---|---|
| `--sev-amber` / `--amber-soft` / `--amber-border` / `--amber-deep` | `#B54708` · `#FEF3E2` · `#F8D5A4` · `#92400E` | Attention, but not urgent |
| `--sev-red` / `--red-soft` / `--red-border` / `--red-deep` | `#B42318` · `#FBE8E5` · `#F5C5BE` · `#911C13` | Overdue, failed, blocked |

There are no more colors than these. If you need another meaning, first check whether one of the existing ones already carries it.

## Spacing, corners, shadows

| Token | Value | What for |
|---|---|---|
| `--pad` | `20px` | Inner padding of cards |
| `--gap` | `14px` | Spacing between cards |
| `--shadow-1` | `0 1px 2px rgba(13,31,26,.04)` | Resting surfaces |
| `--shadow-2` | `0 4px 16px rgba(13,31,26,.06)` | Highlighted surfaces |
| `--ease` | `cubic-bezier(.2,0,0,1)` | Every movement, so nothing feels hectic |

**Radii:** `999px` for chips and pills, `10px` for cards and panels, `6px` for small surfaces like code chips. No more steps than that are needed.

**Typeface:** `Inter`, if it is on the machine, otherwise the system font. Deliberately not loaded from outside, so the file works offline.

## Patterns

**Card:** white surface, `--border`, `--shadow-1`, `--pad` inside. Heading in `--text`, content in `--text-2`, labels small in `--text-3`.

**Status at a glance:** a colored dot or a colored edge, never a colored block. Set up is green, not set up is grey, not red. Red is reserved for broken, not for unfinished.

**Technical values** (commands, paths, keys) always in monospace and usually on their own calm surface. The user should see immediately what they can copy.

**Empty areas** get a calm sentence about what will appear there and how to fill it. Never an empty field and never an error message when there is simply nothing there yet. A freshly set-up system must not look like a broken one.

## Limits

The dashboard is a single HTML file that works on a double-click. Therefore: **no external fonts, no icon libraries, no CDN, no build step.** Icons are embedded SVG, fonts are system fonts. Whoever builds in an external dependency makes the file useless offline.
