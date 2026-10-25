---
id: omi-skill-ui-a11y-review
group: ui
description: Use when reviewing or building web UI for accessibility: labels, contrast, keyboard, focus, semantics, motion.
tokens: 689
tools: Read, Grep
source_repo: https://www.w3.org/TR/WCAG22/
source_ref: 2.2
source_file: WCAG 2.2 Recommendation (level A and AA basics)
source_license: W3C Document License
source_use: rewrite
---
<!-- Own wording from the public WCAG 2.2 basics (https://www.w3.org/TR/WCAG22/). No text copied. -->
# UI accessibility review

## When to use
- A UI change adds or edits forms, buttons, links, dialogs, navigation, images, color or animation.

## When not to use
- Visual styling choices (omi-skill-ui-direction); native apps; a full certified audit.

## Inputs
- Changed UI files and, if possible, the running page.

## Steps
1. Semantics: use `button` for actions, `a` for navigation, landmarks (`nav`, `main`), one `h1`, headings in order, lists for lists. A `div` with a click handler is a defect.
2. Names: every input has a visible `label` tied by `for`/`id` (placeholder is not a label); icon-only buttons have `aria-label`; meaningful images have specific `alt`, decorative ones `alt=""`. Prefer native elements over ARIA.
3. Contrast: text 4.5:1 against its background (large text 3:1); UI borders, icons and focus rings 3:1. Information never by color alone (add text, icon or underline).
4. Keyboard: everything works with Tab, Shift+Tab, Enter, Space, Esc. Tab order follows reading order; no positive `tabindex`; no keyboard trap; modals trap focus while open and return it on close; provide a skip-to-content link.
5. Focus: a visible focus ring on every control, never `outline: none` without a replacement; a focused element is not hidden under a sticky header.
6. Targets and zoom: pointer targets at least 24x24 CSS px; the page works at 200% zoom and 320px width without two-way scrolling; do not block pinch zoom.
7. Forms: errors are text next to the field, linked with `aria-describedby`, and say how to fix; required fields are marked in text; autocomplete attributes on personal data fields.
8. Motion: no auto-playing movement over 5 seconds without a pause; honor `prefers-reduced-motion`; nothing flashes more than 3 times per second.
9. Language and titles: `lang` on `html`, a unique page `title`, status messages via `role="status"` or `aria-live`.

## Outputs and evidence
- Findings as `file:line - rule - fix`, ordered by severity (blocks use, hurts use, polish). State what was checked in the browser and what only by reading code.

## Stop and escalate
- Findings need a redesign or a change outside the task scope: report NEEDS SCOPE with the list.

## Tools needed
- Read, Grep; a browser (omi-skill-web-qa) for contrast and focus checks.
