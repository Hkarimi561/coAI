# coAI

A Persian-first (RTL) internal chat and admin UI for a DevOps assistant. Calm, dense, utility-first: white cards on a pale grey page, one blue accent, hairline borders instead of heavy shadows.

## Content fundamentals
- Language is Persian; layout is RTL (`dir="rtl"`). Code, logs and terminal output are always LTR (`pre`, `code`, `.ltr`).
- Numbers in UI copy use Persian digits (`toLocaleString("fa-IR")`).
- Short, direct labels ("قبلی", "بعدی", "بستن"). No emoji.

## Visual foundations
- **Color**: semantic tokens only, never raw hex. `background` page, `card` surfaces, `muted` fills, `border` hairlines, `primary` blue for actions and focus, `danger`/`success`/`warning` for state. Light and dark themes (`dark` class on html).
- **Type**: Vazirmatn (sans) with Segoe UI/Tahoma fallbacks; JetBrains Mono for code. Base size 14px.
- **Shape**: radius-md 8px for controls, radius-lg 12px for cards and dialogs, full for badges and switches. Only shadow-sm, on cards.
- **Focus**: 2px primary ring with 2px offset in background color on every focusable element.
- **Motion**: color transitions only; theme change cross-fades 0.4s.
- Use logical properties (ps-*, ms-*, start-*, border-s) so RTL and LTR both work.

## Using the components
The source is a Tailwind + Radix + class-variance-authority app (`frontend/src/components/ui`). Tailwind colors map to CSS variables: `bg-primary`, `text-muted-foreground`, `border-border`, `bg-card`, `text-danger`, with opacity modifiers like `bg-primary/10`.

Components: Button, Badge, Card, Input, Switch, Tabs (see each README).

## Not synced
Components have static previews only (no live bundle). Dialog, Textarea/Select, Spinner, ErrorBanner, Empty, Pager and the chat/admin feature components are not covered. Vazirmatn font files were not copied. Static badge tints are simplified to the muted background.
