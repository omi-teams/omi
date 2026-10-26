# Style presets (optional; read only when the task asks for a direction)

Pick one preset and one layout, then keep to them for the whole task. Do not repeat the same pair across consecutive tasks.

## Looks
- Dark glass (SaaS, AI, tech): near-black `#050505`, soft radial gradient glows, translucent cards with `border-white/10`, wide geometric grotesk.
- Editorial (lifestyle, real estate, agency): warm cream `#FDFBF7`, sage or espresso accents, large variable serif headings, faint grain at 3% opacity on a fixed layer.
- Soft structural (consumer, health, portfolio): white or silver-gray, bold grotesk headings, floating components with very diffuse shadows.

## Layouts
- Asymmetric bento: grid with mixed spans (`col-span-8 row-span-2` beside stacked `col-span-4`); reset every span to 1 below 768px.
- Overlapping cascade: stacked cards, slight overlap, optional 2-3 degree rotation; remove rotation and negative margins below 768px (touch targets).
- Editorial split: big type on the left half, scrollable cards or images on the right; stack on mobile.

## Optional details
- Nested card: outer shell (`p-1.5`, hairline ring, large radius) around an inner core with its own background and a smaller concentric radius.
- Floating pill nav detached from the top (`mt-6`, `rounded-full`).
- Pill button with the arrow in its own small circle at the right edge.
- Small uppercase eyebrow tag above section headings (`text-[10px] tracking-[0.2em]`).
- Staggered fade-up on scroll entry, 800ms or more, 100ms steps.
