# Design System -- Graft

## Product Context
- **What this is:** AI-native BI report translation tool (hub-and-spoke architecture)
- **Who it's for:** Enterprise BI teams, data architects, migration leads -- broad audience for product vision
- **Space/industry:** Data infrastructure, BI migration, enterprise analytics
- **Project type:** Conceptual slide deck / product vision presentation
- **Sibling:** Crawl (getcrawl.dev) -- Step 0, pre-migration intelligence. Graft is Step 1.
- **Parent brand:** Digital Rain Technologies (digitalrain.studio) -- solarized palette, monochrome system, dark-mode-first

## Memorable Thing
"We know what we're doing. Enterprise veterans. Surgical approach. Build the 20% of software that solves 80% of the problem. Data lineage and fidelity first. Reasoning last."

## Aesthetic Direction
- **Direction:** Industrial-Editorial -- precision engineering meets authoritative presentation
- **Decoration level:** Minimal -- typography and whitespace do the work. The hub-and-spoke diagram IS the decoration.
- **Mood:** Surgical precision. The visual equivalent of a surgeon's tools laid out on a tray: clean, intentional, nothing extra. Not flashy startup, not corporate gray.
- **Reference sites:** getcrawl.dev (sibling -- IBM Plex, light mode, ultra-minimal), digitalrain.studio (parent -- solarized, Matrix aesthetic, dark mode)

## Typography
- **Display/Hero:** Instrument Serif -- editorial authority without stuffiness. Serifs say "we have history" while optical sizing keeps it modern. Differentiates from geometric-sans-only data infra tools.
- **Body:** DM Sans -- geometric, clean, reads at distance. Tabular-nums for data slides. Not Inter, not system-ui.
- **UI/Labels:** DM Sans (same as body, weight 600 for labels)
- **Data/Tables:** DM Sans with tabular-nums feature, or JetBrains Mono for dense data
- **Code:** JetBrains Mono -- ligatures OFF (surgical precision, not decoration)
- **Loading:** Google Fonts CDN: `https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=Instrument+Serif:ital@0;1&family=JetBrains+Mono:wght@400;500&display=swap`
- **Minimum font size:** 18px (text-lg) for all body/label text. Smaller only for uppercase tracking labels (14px minimum).
- **Scale:** 14px (label) / 18px (body) / 24px (large body) / 32px (h3) / 40px (h2) / 48px+ (h1/hero)

## Color
- **Approach:** Restrained -- one accent color. When cyan appears, it MEANS something: the hub, the IR, the living translation.
- **Background:** #0a1628 (deep navy-black, premium feel)
- **Surface:** #132238 (elevated cards, panels)
- **Primary text:** #c8d6e5 (soft blue-white, easy on eyes)
- **Muted text:** #5a7a9b (steel blue, secondary content)
- **Text emphasis:** #e8f0f8 (headings, important text)
- **Accent (primary):** #2aa198 (solarized cyan -- the hub color, the "alive" signal)
- **Accent dim:** rgba(42, 161, 152, 0.15) (accent backgrounds, highlights)
- **Accent secondary:** #b58900 (solarized yellow -- warnings, fidelity review scores)
- **Error/risk:** #dc322f (solarized red -- point-to-point chaos, failures)
- **Border:** #1e3454 (subtle dividers)
- **Dark mode:** Primary. This IS the dark mode palette.
- **Light mode strategy:** Warm paper tones (#fdf6e3 background) if ever needed, but dark mode is default.

## Spacing
- **Base unit:** 8px
- **Density:** Spacious -- slides need air. Negative space is structural, not wasteful.
- **Scale:** 2xs(2) xs(4) sm(8) md(16) lg(24) xl(32) 2xl(48) 3xl(64)

## Layout
- **Approach:** Grid-disciplined -- strict alignment, generous whitespace
- **Grid:** Asymmetric hero for hub-and-spoke diagram, consistent margins elsewhere
- **Max content width:** 1200px
- **Border radius:** sm:4px, md:6px, lg:8px (restrained, not bubbly)
- **Slide aspect ratio:** 16:9

## Motion
- **Approach:** Minimal-functional -- only transitions that aid comprehension
- **Easing:** enter(ease-out) exit(ease-in) move(ease-in-out)
- **Duration:** micro(50-100ms) short(150-250ms) medium(250-400ms)
- **One expressive moment:** Hub-and-spoke build animation (spokes radiating from center)

## Key Visual Concepts
- **Hub-and-spoke diagram:** Central "Common IR" node in cyan, platform nodes in muted steel blue, spokes in cyan. Contrast with red spaghetti N-squared point-to-point.
- **Pipeline:** ingest -> analyze -> translate -> validate -> export. Active step highlighted in accent.
- **Fidelity badges:** green/cyan for exact, yellow for review, red for no equivalent.
- **Crawl + Graft stack:** Step 0 (muted) -> Step 1 (accent-highlighted). Same family, different weight class.

## Decisions Log
| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-05-26 | Initial design system created | Created by /design-consultation for conceptual slide deck emphasizing hub-and-spoke architecture |
| 2026-05-26 | Instrument Serif for display | Deliberate risk: serifs differentiate from geometric-sans-only data infra tools, signal enterprise authority |
| 2026-05-26 | Navy-black (#0a1628) over solarized base03 | Graft needs its own identity while inheriting Digital Rain DNA. Deeper blue feels more premium. |
| 2026-05-26 | Single accent color discipline | Cyan means the hub/IR/alive. Restraint makes every colored element deliberate. |
| 2026-05-26 | 18px minimum font size | User preference for larger, more readable text across all slide content |
