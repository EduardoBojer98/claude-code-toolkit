---
name: web-dev-standards
description: Personal web dev standards for every website, theme, plugin or web app built for this user (WordPress block/classic themes, plugins, WooCommerce, HTML/CSS/JS, React, Next.js, Tailwind, SCSS). Use on ANY web project, page, component, theme or code review, even when not named.
---

# Web Dev Standards

These are my standards for every web project. Apply them by default, without being asked.
When a project has its own conventions (an existing theme, a client's codebase), follow those
for style and naming, but never drop below the accessibility, security and performance floors here.

**Order of work on any project:**
1. Read what exists (theme/project structure, `theme.json`, `package.json`, `composer.json`, README).
2. Check current docs with Context7 for any library/framework API you're about to use
   (WordPress, Gutenberg, Next.js, React, Tailwind). Don't trust memory for APIs.
3. Pick a design direction (see Design) before writing markup.
4. Build mobile-first, in small commits.
5. Verify visually with Playwright (or the browser) at 375px, 768px and 1280px, light and dark.
6. Run the Definition of Done checklist at the bottom. A project isn't finished until it passes.

Choose the stack per project. Default to the lightest thing that does the job well:
plain HTML/CSS/JS for brochure sites, a block theme for WordPress, Next.js only when the project
needs routing, data fetching or app-like interactivity. Tailwind or SCSS are both fine; pick one per project
and don't mix them.

---

## 1. Design

**Goal:** modern, clean, intentional. It must not look like a template or a generic AI landing page.

### Direction first
- Before coding, write 2–3 lines: the audience, the tone (e.g. "editorial, calm, warm neutrals"),
  and one distinctive element (a type pairing, a bold grid, a signature color, an illustration style).
- Use the `frontend-design` skill for direction on new UI or redesigns.
- Avoid the generic look: purple-to-blue gradients, centered hero + three icon cards + testimonial
  slider by default, glassmorphism everywhere, stock "team high-fiving" imagery, emoji as icons,
  everything rounded-2xl with drop shadows.

### Design tokens (always)
All values come from tokens defined once as CSS custom properties (or `theme.json` presets in WordPress,
or `@theme` in Tailwind v4). No magic numbers in components.

```css
:root {
  /* Color: 1 brand, 1 accent, neutrals, semantic. Max ~5 hues. */
  --color-bg: oklch(98.5% 0.005 90);
  --color-surface: oklch(96% 0.008 90);
  --color-text: oklch(22% 0.02 260);
  --color-text-muted: oklch(45% 0.02 260);
  --color-border: oklch(88% 0.01 260);
  --color-primary: oklch(52% 0.16 255);
  --color-primary-contrast: #fff;
  --color-accent: oklch(72% 0.15 65);
  --color-success: oklch(55% 0.14 150);
  --color-danger: oklch(55% 0.19 25);

  /* Type: fluid scale (~1.25 ratio) */
  --font-sans: "Inter Variable", system-ui, sans-serif;
  --font-display: "Fraunces Variable", Georgia, serif;
  --step--1: clamp(0.83rem, 0.8rem + 0.15vw, 0.9rem);
  --step-0:  clamp(1rem, 0.95rem + 0.25vw, 1.125rem);
  --step-1:  clamp(1.25rem, 1.15rem + 0.5vw, 1.5rem);
  --step-2:  clamp(1.56rem, 1.38rem + 0.9vw, 2rem);
  --step-3:  clamp(1.95rem, 1.6rem + 1.6vw, 2.75rem);
  --step-4:  clamp(2.44rem, 1.9rem + 2.6vw, 3.75rem);

  /* Space: 4px base scale */
  --space-1: 0.25rem; --space-2: 0.5rem; --space-3: 0.75rem; --space-4: 1rem;
  --space-6: 1.5rem;  --space-8: 2rem;   --space-12: 3rem;   --space-16: 4rem; --space-24: 6rem;

  --radius-sm: 4px; --radius-md: 8px; --radius-lg: 16px;
  --shadow-sm: 0 1px 2px oklch(0% 0 0 / 0.06);
  --shadow-md: 0 4px 16px oklch(0% 0 0 / 0.08);
  --container: 72rem; --measure: 65ch;
  --ease-out: cubic-bezier(0.22, 1, 0.36, 1);
  --duration: 200ms;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) { /* redefine color tokens only */ }
}
:root[data-theme="dark"] { /* same dark values, for a manual toggle */ }
```

### Layout & hierarchy
- Mobile-first; layout with Grid for page structure, Flexbox for components. Use `gap`, never margins between siblings in a flex/grid.
- Container queries for components that live in different-width contexts.
- One clear focal point per section. Hierarchy comes from size, weight, color and space, not from boxes and borders.
- Generous whitespace: section padding at least `--space-16` on desktop. Body text at most `--measure` wide.
- Max 2 font families (often 1 variable font is enough). Body 16–18px, line-height 1.5–1.7; headings 1.1–1.25, tighter letter-spacing on large display type.
- Consistent alignment; deliberate asymmetry is fine, accidental misalignment is not.

### Motion
- Subtle and purposeful: 150–300ms, ease-out, on `transform`/`opacity` only.
- Always respect `@media (prefers-reduced-motion: reduce)` (disable non-essential motion).
- No scroll-jacking. No animation library for things CSS can do (transitions, `@starting-style`, scroll-driven animations with a fallback, View Transitions API).

### Dark mode
Provide it when it fits (apps, dashboards, dev/tech audiences, or the client asks). Implement by swapping color tokens only, and check contrast in both modes.

---

## 2. Code quality (all projects)

### HTML
- Semantic landmarks: `header`, `nav`, `main` (one), `aside`, `footer`; `article`/`section` with headings.
- One `h1` per page; no skipped heading levels.
- Buttons for actions, links for navigation. Never `div` with a click handler.
- Native elements first (`<dialog>`, `<details>`, `popover`, `<input type="...">`) before custom JS widgets.

### CSS
- No inline styles (except dynamic values set via a CSS custom property, e.g. `style="--progress: 40%"`).
- Organize with cascade layers: `@layer reset, tokens, base, layout, components, utilities;`
- Modern features: native nesting, `:where()`/`:is()` to keep specificity low, `clamp()`, logical properties (`margin-inline`, `padding-block`), `aspect-ratio`, `:has()`, container queries.
- Naming: BEM-ish (`.card`, `.card__title`, `.card--featured`) or Tailwind utilities, consistently per project.
- No `!important` (except utilities/overrides of third-party CSS, with a comment). No IDs for styling.
- No framework or library for something a few lines of CSS can do.
- **Tailwind v4:** CSS-first config with `@theme` for tokens; extract repeated utility groups into components, not `@apply` everywhere.
- **SCSS:** use `@use`/`@forward` (not `@import`), partials per component, tokens still output as CSS custom properties.

### JavaScript / TypeScript
- ES modules, small single-purpose functions, `const` by default, early returns.
- TypeScript for React/Next.js and any app with real logic.
- No jQuery in new code. Progressive enhancement: the page works (content readable, links work) before JS loads.
- Event delegation for lists, `AbortController` to clean up listeners, no global variables.
- Handle errors and loading/empty states explicitly.
- Comments explain *why*, not *what*. JSDoc on exported functions.
- DRY: if code is repeated 3 times, extract it. Don't abstract on the first use.
- Formatting and linting: Prettier + ESLint (+ Stylelint for CSS) configured in the repo.

### Naming
- Files: `kebab-case` (CSS/JS/PHP templates), `PascalCase.tsx` for React components.
- JS: `camelCase` variables/functions, `PascalCase` components/classes, `UPPER_SNAKE` constants.
- PHP (WordPress): `snake_case` functions prefixed with the theme/plugin slug, `Class_Name` classes per WPCS.

---

## 3. WordPress

Target the current WordPress release (7.x in late 2026; confirm with Context7/release notes). PHP minimum
supported by WP is 7.4, but write for **PHP 8.2+** (8.3 recommended) and declare it in the theme header.

### Theme approach
- **Default: block theme** with `theme.json` (version 3) as the single source of design tokens:
  palette, font families/sizes (fluid), spacing scale, layout widths, shadows, border radii.
  Map tokens 1:1 to the CSS custom properties WordPress generates (`--wp--preset--color--primary`, etc.).
- Define custom breakpoints, element states (`:hover`, `:focus`) and responsive styles in `theme.json`
  where the current WP version supports it, before reaching for custom CSS.
- Templates and parts in `/templates` and `/parts`; reusable layouts as **patterns** in `/patterns`
  (with `Categories`, `Keywords`, `Block Types` headers). Lock structure where clients shouldn't break it
  (`templateLock`, `lock` attributes) but leave content editable.
- Style variations in `/styles` for alternate palettes instead of hard-coded options.
- **Never edit WordPress core or a parent/third-party theme.** Customize via a child theme, the starter theme, or a site plugin.
- Classic themes: only when a project requires it; then use a child theme and `add_theme_support()` for modern features.

### Custom blocks
- `block.json` with `"apiVersion": 3` (required for the iframed editor), `@wordpress/scripts` for builds,
  `register_block_type( __DIR__ . '/build/block-name' )`.
- Prefer dynamic blocks (PHP `render.php`) for anything data-driven; use the Interactivity API for front-end interactivity instead of ad-hoc JS.
- Prefer core blocks + patterns + Block Bindings before building a custom block.

### Functionality placement
- Presentation in the theme. Content structures (CPTs, taxonomies, meta, shortcodes, integrations)
  in a **site-specific plugin** (or `mu-plugin`) so they survive a theme change.

### Coding standards & structure
- WordPress Coding Standards (WPCS 3.x) via PHPCS, configured in `phpcs.xml.dist`; PHPStan with WordPress stubs for larger code.
- Prefix everything (functions, hooks, options, handles, CSS classes for custom blocks) with the project slug, or use namespaces.
- `functions.php` stays small: it only requires files from `/inc` (setup, enqueue, blocks, patterns, security, etc.).
- Everything translatable with the theme's text domain: `__()`, `esc_html__()`, `_x()`, `_n()`.

### Enqueueing
- Always `wp_enqueue_style()` / `wp_enqueue_script()` on the right hook (`wp_enqueue_scripts`, `enqueue_block_assets`, `enqueue_block_editor_assets`).
- Version assets with the build's `*.asset.php` file (dependencies + hash) or `filemtime()` in dev.
- Load scripts with `'strategy' => 'defer'` (or `async`) and in the footer. No hard-coded `<script>`/`<link>` tags in templates.
- Per-block styles with `wp_enqueue_block_style()` so CSS only loads where a block is used.

### Security (non-negotiable)
- **Sanitize on input** (`sanitize_text_field`, `sanitize_email`, `absint`, `wp_kses_post`, …).
- **Escape on output, late** (`esc_html`, `esc_attr`, `esc_url`, `wp_kses`, `esc_js` rarely). Every echo is escaped.
- **Nonces** on every form and AJAX/REST action (`wp_nonce_field` / `check_admin_referer` / `wp_verify_nonce`).
- **Capability checks** (`current_user_can`) before any privileged action; REST routes always have a real `permission_callback`.
- `$wpdb->prepare()` for every query with variables. Prefer WP APIs over raw SQL.
- No `eval`, no `extract()`, no direct file includes from user input.

### Hooks, not hacks
- Change behavior with actions/filters; never patch plugin or core files.
- Use WP APIs (Settings API, Options, Transients, REST API, `WP_Query`) instead of custom equivalents.
- Cache expensive queries with transients or the object cache.

### Client-friendly & lean
- Minimal plugins: only well-maintained, necessary ones. Each one is justified in the README.
- Editors edit content through blocks/patterns, not code. Disable or lock what they shouldn't touch.
- Remove bloat: emoji scripts, unused block styles, oEmbed discovery if not needed, unused core block patterns.
- Local dev with Lando; keep `.lando.yml` in the repo. Never commit `wp-config.php`, uploads or `.env`.

---

## 4. Custom projects (HTML/CSS/JS, React, Next.js)

### Structure
- Plain site: `/src` (`/css`, `/js`, `/images`, `/fonts`), Vite for dev server and build if anything needs bundling.
- Next.js (App Router): `app/` for routes; `components/` (`ui/` primitives + feature components),
  `lib/` (utilities, data access), `styles/`, `public/`. Server Components by default; `"use client"` only where interactivity requires it.
  Use `next/image`, `next/font`, and the Metadata API. Check Context7 for the current Next.js version's APIs.
- Components: one component per file, props typed, no business logic in presentational components.

### Config & secrets
- Secrets in environment variables only (`.env.local`, never committed); commit an `.env.example` with placeholder values.
- Validate env vars at startup (e.g. zod). In Next.js, only `NEXT_PUBLIC_` vars reach the browser, so never put secrets there.

### Git
- Initialize Git from the first file. `.gitignore` for `node_modules`, builds, `.env*`, OS files, `vendor/`.
- Small commits with Conventional Commit messages: `feat:`, `fix:`, `style:`, `refactor:`, `docs:`, `chore:`.
- Work on branches (`feat/header-nav`), merge to `main` via PR when using GitHub.

### README (every project)
What it is, tech stack, requirements, setup (`lando start` / `npm install && npm run dev`),
environment variables, build/deploy steps, folder structure, and for WordPress: required plugins and how clients edit content.

---

## 5. Accessibility (WCAG 2.2 AA minimum)

- Contrast: text 4.5:1, large text (24px+, or 18.66px+ bold) and UI components/focus indicators 3:1, in light AND dark mode.
- Every meaningful image has descriptive `alt`; decorative images use `alt=""`.
- Full keyboard support: logical tab order, no traps, `Esc` closes overlays, focus moves into and returns from dialogs.
- Visible focus on everything interactive: `:focus-visible { outline: 2px solid var(--color-primary); outline-offset: 2px; }`. Never `outline: none` without a replacement.
- Focus must not be hidden behind sticky headers (`scroll-padding-top`).
- Targets at least 24×24px (aim for 44×44px on touch).
- Every input has a visible `<label>`; errors are announced in text and linked with `aria-describedby`, not just shown by color.
- Skip link to `#main`, `lang` on `<html>`, meaningful link text (no "click here").
- ARIA only when native HTML can't do it; test with the `a11y-enforcer` skill and a keyboard pass.

---

## 6. Performance (Core Web Vitals "good" at p75)

Targets: **LCP ≤ 2.5s, INP ≤ 200ms, CLS ≤ 0.1**; Lighthouse Performance ≥ 90 on mobile.

- Images: AVIF/WebP with fallback, responsive `srcset`/`sizes`, explicit `width`/`height` (or `aspect-ratio`), `loading="lazy"` below the fold.
  The LCP image is **not** lazy-loaded and gets `fetchpriority="high"`.
- Fonts: self-hosted WOFF2 variable fonts, `font-display: swap`, preload only the one or two critical files, subset when possible.
- JS: ship as little as possible; `defer` everything; no render-blocking scripts; code-split in apps; avoid heavy libraries (check bundle size before adding a dependency).
- CSS: critical CSS stays small; per-block/per-component loading in WordPress.
- Avoid layout shift: reserve space for embeds, ads, cookie banners and late content.
- Cache: long cache headers on hashed assets; page caching on WordPress hosting.
- Measure with the `perf-profiler` skill (Lighthouse/PageSpeed) before and after changes.

---

## 7. SEO

- Unique `<title>` (≈50–60 chars) and meta description (≈150–160) per page; canonical URL; Open Graph + Twitter card tags.
- Heading outline that reflects content (one `h1`).
- JSON-LD structured data appropriate to the page (Organization/LocalBusiness, WebSite, BreadcrumbList, Article, Product, FAQ only if visible on the page). Validate it.
- Clean, lowercase, hyphenated URLs; WordPress permalinks set to `/%postname%/`.
- XML sitemap (WP core sitemap or the SEO plugin's) and a sane `robots.txt`; noindex staging sites.
- Descriptive internal links and image file names. Use `searchfit-seo` skills to check.

---

## 8. Security (all projects)

- No secrets, keys or passwords in code or Git history. Rotate anything that leaks.
- Validate and sanitize all input on the server, even when the client validates too. Escape all output.
- Use HTTPS everywhere; set security headers where the host allows (CSP, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, HSTS).
- Keep dependencies current: run `npm audit` / `composer audit`, and keep WP core, themes and plugins updated. Remove unused packages and plugins.
- Least privilege for accounts, API tokens and database users.

---

## 9. Definition of Done (run before calling any project finished)

Report the result of each item to the user; fix failures before saying it's done.

**Design**
- [ ] Checked visually at 375 / 768 / 1280px (Playwright screenshots); no overflow or horizontal scroll
- [ ] Consistent spacing, type scale and colors, all from tokens; no stray hard-coded values
- [ ] Dark mode (if included) looks right and passes contrast
- [ ] Doesn't look like a generic template; the design direction is visible

**Code**
- [ ] Semantic HTML; no inline styles; no duplicated code; no console errors or warnings
- [ ] Linters pass (ESLint / Stylelint / PHPCS-WPCS); formatted with Prettier
- [ ] No leftover debug code, commented-out blocks or unused files/dependencies

**WordPress** (if applicable)
- [ ] Core and parent themes untouched; assets enqueued properly; `functions.php` lean
- [ ] All input sanitized, all output escaped, nonces and capability checks in place
- [ ] Custom blocks on apiVersion 3 and working in the iframed editor
- [ ] A client can edit all content in the editor without touching code; works with `WP_DEBUG` on and no notices

**Accessibility**
- [ ] Keyboard-only walkthrough works; focus always visible; skip link present
- [ ] Contrast AA; alt text; labels; heading order; `a11y-enforcer` check passes

**Performance**
- [ ] Lighthouse mobile Performance ≥ 90; LCP / INP / CLS in "good" range
- [ ] Images modern format, sized and lazy where appropriate; fonts optimized

**SEO**
- [ ] Titles, descriptions, canonical, OG tags; valid JSON-LD; sitemap; robots; clean URLs

**Security & delivery**
- [ ] No secrets in code; `.env.example` present; dependencies audited
- [ ] README complete; Git history clean with meaningful commits
