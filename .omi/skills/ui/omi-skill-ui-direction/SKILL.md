---
id: omi-skill-ui-direction
group: ui
description: Use when building or restyling a web UI and it must not look generic: fonts, spacing, color, shadows, states, complete output.
tokens: 1107
tools: Read, Edit, Write
source_repo: https://github.com/leonxlnx/taste-skill
source_ref: 1.0.0
source_file: soft-skill, redesign-skill, output-skill
source_license: MIT
source_use: adapt
---
<!-- Adapted from the Taste plugin (https://github.com/leonxlnx/taste-skill), MIT, Copyright (c) 2026 Leonxlnx.
     source_ref 1.0.0 is the installed plugin version, not a commit: upstream was restructured later and is not pinned to it.
     Changes: personas, hype and fluff removed; only concrete rules kept; three skills merged into one. -->
# UI direction

## When to use
- New page or component, or a redesign of an existing one, where the result looks like a template.

## When not to use
- Accessibility checks only (omi-skill-ui-a11y-review); backend or data work; a design system the project already defines (follow that instead).

## Inputs
- Target files, the project's framework and styling method (check the Tailwind version before editing config), existing tokens.
- Optional: `references/style-presets.md` in this skill's directory. Read it only if the task asks for a preset or a direction.

## Steps
1. Scan the stack. Work inside it: no framework or styling migration, no new library before checking the dependency file.
2. Diagnose before editing; list each generic pattern found. Fix in this order: fonts, colors, hover/active/focus states, layout and spacing, generic components, loading/empty/error states, typography polish.
3. Fonts: replace browser defaults, Inter, Roboto, Arial. Use one display face (Geist, Outfit, Satoshi) and one body face; serif headings for editorial work. Use weights 500 and 600, not only 400 and 700. Tighten tracking on large headings, widen it on small caps. Body width about 65 characters. `tabular-nums` for data. `text-wrap: balance` on headings.
4. Spacing: container max-width 1200-1440px; section padding at least `py-24` on marketing pages (denser on dashboards); align titles, prices and buttons across sibling cards; pin card buttons to the bottom; vary radius (inner tighter than outer). Use `min-height: 100dvh`, never `100vh`. Use CSS Grid, not flex percentage math. Below 768px collapse to one column, `px-4`.
5. Color: one accent, saturation under 80%; one gray family tinted to one hue; no pure `#000`; no purple-blue AI gradient; no lone dark section on a light page.
6. Shadows and surfaces: no harsh black shadows (`rgba(0,0,0,.3)`); tint soft, diffuse shadows to the background hue, one light direction; hairline borders (`border-white/10`) instead of heavy gray 1px; cards only when elevation shows hierarchy. `backdrop-blur` only on fixed or sticky layers; noise only on a fixed `pointer-events-none` layer.
7. Motion: 200-300ms on every interactive element, custom cubic-bezier (for example `0.32,0.72,0,1`), no `linear`. Animate `transform` and `opacity` only. Press feedback `scale(0.98)`. Use IntersectionObserver for reveals, never a scroll listener. Respect `prefers-reduced-motion`.
8. States and content: hover, active, visible focus, loading (skeleton), empty, error (inline, no `alert()`), current nav item, no `#` links. Real-looking copy: no Lorem Ipsum, no "John Doe", no "Acme", no "Elevate/Seamless/Unleash", no "Oops!", sentence case headings.
9. Components: avoid three equal feature cards, accordion FAQ by default, sun/moon toggle as the only option, modals for simple actions, rocket and shield icons; keep one icon set and one stroke width. Use semantic tags (`nav`, `main`, `section`), z-index scale instead of 9999, favicon, meta tags, skip link.
10. Complete output: deliver every file or component asked for, whole. No `// ...`, `// rest of code`, `TODO` or "similar to above". Count the deliverables first and compare before replying. If the limit is near, stop at a clean break (end of file) and say what remains.

## Outputs and evidence
- Changed files, plus a short list of what was replaced and why. Screenshot at 375px and 1280px when a browser is available (omi-skill-web-qa).

## Stop and escalate
- The fix needs a framework migration, a new dependency or files outside the task scope: stop and report NEEDS SCOPE.
- Brand fonts or assets are required but missing: ask, do not invent them.

## Tools needed
- Read, Edit, Write.
