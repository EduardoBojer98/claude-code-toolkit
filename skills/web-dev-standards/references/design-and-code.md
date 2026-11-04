# Design and code quality

Part of web-dev-standards. Load for new pages, sections, redesigns, UI review or front-end code.

## Design

- **Direction before markup:** 2–3 lines naming audience, tone and one distinctive element (type pairing, grid, colour, imagery). Choices serve the brand and the conversion goal; these are defaults, not bans.
- Avoid the generic AI look unless the brand calls for it: purple-blue gradients, centred hero + three icon cards by default, glassmorphism everywhere, emoji as icons, uniform rounded cards with shadows.
- **Tokens:** every colour, type step, space, radius, shadow and duration comes from tokens defined once (CSS custom properties, `theme.json` presets, Tailwind v4 `@theme`, Elementor global colours/fonts, Shopify theme settings). No magic numbers in components.
- Type: at most 2 families; fluid scale (~1.2–1.25); body 16–18px, line-height 1.5–1.7; measure ≤ 65–75ch.
- Spacing on a 4px base; one focal point per section; hierarchy from size, weight, colour and space before boxes.
- Mobile-first; Grid for page layout, Flexbox for components, `gap` between siblings, container queries where components move between contexts.
- **Motion** (in this order; stop at the first that does the job):
  1. CSS transitions/keyframes: 150–300ms UI, 400–700ms entrances, ease-out in, ease-in out; `transform`/`opacity` only.
  2. Scroll-driven animations (`animation-timeline: view()`/`scroll()`) inside `@supports (animation-timeline: view())`, content fully visible without them.
  3. View Transitions: same-document `document.startViewTransition()`; multi-page sites `@view-transition { navigation: auto; }`. Progressive enhancement only.
  4. A library only when 1–3 can't: GSAP (free, incl. ScrollTrigger/SplitText) for timelines and pinned scroll stories; Motion for React state-driven animation. One library per project, loaded only on pages that use it.
  - Always: `@media (prefers-reduced-motion: reduce)` swaps movement for a fade or nothing; never animate the LCP element in; no scroll-jacking; nothing autoplays longer than 5s without a pause control (WCAG 2.2.2).
- Microcopy: verb-first button labels ("Book a call", not "Submit"); errors say what happened and how to fix it, never blame; every input has a visible label; no spinner under ~300ms, skeletons for longer loads.
- E-commerce: price, delivery and returns visible near the buy button; trust signals near decisions; no surprise costs at checkout.
- Dark mode when it fits (apps, tech audiences, client request): swap colour tokens only; check contrast in both modes.

## Code quality (all projects)

- HTML: semantic landmarks, one `main`; buttons for actions, links for navigation, never a clickable `div`; native `<dialog>`, `<details>`, `popover` before custom widgets. Baseline newly available (use with a fallback): CSS anchor positioning for tooltips and menus, `@scope`, container style queries, `field-sizing: content`; customizable `<select>` only as progressive enhancement.
- CSS: no inline styles (except custom-property values); cascade layers (`reset, tokens, base, layout, components, utilities`); low specificity with `:where()`; logical properties; no `!important` except third-party overrides, with a comment; no IDs for styling; one approach per project (BEM-ish or Tailwind, SCSS with `@use`).
- JS: ES modules, `const`, early returns, no jQuery in new code, progressive enhancement, `AbortController` to clean up listeners, explicit loading/empty/error states.
- Naming: `kebab-case` files, `PascalCase.tsx` components, `camelCase` JS, prefixed `snake_case` PHP functions per WPCS. Comments explain why. Extract on the third repetition, not the first.
- Prettier + ESLint (+ Stylelint) configured in the repo.

