---
name: web-dev-standards
description: Personal web design and development standards and routing for this user's client work - design direction, accessibility, performance, security, Definition of Done, and stack rules for WordPress (block themes, Elementor, ACF, WooCommerce), Shopify (Liquid, metafields, metaobjects), nopCommerce (.NET plugins), React + Vite + TypeScript + Tailwind, and plain HTML/CSS/JS. Use when building, designing, fixing or reviewing a website, theme, plugin, store or web app.
---

# Web Dev Standards

_Version 2.0 · 2026-10-22 · Source of truth: github.com/EduardoBojer98/claude-setup (v1.0 in archive/)_

Apply by default. When a project has its own conventions or a `CLAUDE.md`, follow them for style and
naming, but never go below the accessibility, security and performance floors here.

## 1. How to work

- **Read first:** the project's `CLAUDE.md`, then only the files the task touches. Search for symbols before opening whole files.
- **Size the effort:**
  - Small edit → do it, verify it, report in a line. No plan, no extra skills.
  - Feature → read the relevant code, check docs once, build the smallest reliable solution, run related tests, report.
  - Migration, security work, unfamiliar system → short written plan, change in steps, test each step.
- **Docs:** check APIs with Context7 before using them; don't trust memory. Use these IDs directly (no lookup):
  Elementor `/elementor/elementor-developers-docs` ·
  ACF `/websites/advancedcustomfields_resources` · nopCommerce `/nopsolutions/nopcommerce-docs`.
  Shopify → the Shopify Dev MCP when available. Reuse what was looked up earlier in the session.
- **No helper agents** unless the task splits into independent parts. No new dependency without a reason.
- **Never claim** a test passed, a page renders or a deploy worked without having run or seen it.
- **No vendor promotion** (tool or SaaS plugs) in client-facing output.
- Respect the platform: no React patterns in WordPress/Shopify, no Next.js advice in Vite apps, no new framework in an existing project.

## 2. Routing — load only what the project needs

| Signal | Use | Don't use |
|---|---|---|
| `theme.json`, `block.json`, custom WP plugin, WooCommerce code | §4 WordPress + matching WordPress Dev Skills skill | Shopify/React rules |
| Elementor active, ACF field groups, classic theme | §4 WordPress → Elementor + ACF | Block-theme defaults, WP.org/Freemius skills |
| `.liquid`, `config/settings_schema.json`, `shopify.theme.toml` | §5 Shopify + Shopify Dev MCP | WordPress skills |
| `*.csproj`, `plugin.json` with `SystemName` | §6 nopCommerce | Front-end design skills unless views change |
| `vite.config.*`, `tsconfig.json`, React | §7 React + project's react-best-practices skill | WordPress skills |
| New page, section or redesign | `frontend-design` (or Impeccable `craft` in Claude Code) | More than one design skill at once |
| UI work about to be called done | §10 review: Impeccable `critique`→`polish` if installed, A11y Enforcer, Perf Profiler, Playwright | — |
| A live site to look at, no code | Built-in browser; Chrome only for signed-in client admin | Playwright |
| Scripted screenshots, E2E, visual diffs | Playwright | Chrome extension |

## 3. Design

- **Direction before markup:** 2–3 lines naming audience, tone and one distinctive element (type pairing, grid, colour, imagery). Choices serve the brand and the conversion goal; these are defaults, not bans.
- Avoid the generic AI look unless the brand calls for it: purple-blue gradients, centred hero + three icon cards by default, glassmorphism everywhere, emoji as icons, uniform rounded cards with shadows.
- **Tokens:** every colour, type step, space, radius, shadow and duration comes from tokens defined once (CSS custom properties, `theme.json` presets, Tailwind v4 `@theme`, Elementor global colours/fonts, Shopify theme settings). No magic numbers in components.
- Type: at most 2 families; fluid scale (~1.2–1.25); body 16–18px, line-height 1.5–1.7; measure ≤ 65–75ch.
- Spacing on a 4px base; one focal point per section; hierarchy from size, weight, colour and space before boxes.
- Mobile-first; Grid for page layout, Flexbox for components, `gap` between siblings, container queries where components move between contexts.
- Motion: purposeful, 150–300ms, `transform`/`opacity`, always a `prefers-reduced-motion` fallback; CSS before animation libraries.
- Microcopy: verb-first button labels ("Book a call", not "Submit"); errors say what happened and how to fix it, never blame; every input has a visible label; no spinner under ~300ms, skeletons for longer loads.
- E-commerce: price, delivery and returns visible near the buy button; trust signals near decisions; no surprise costs at checkout.
- Dark mode when it fits (apps, tech audiences, client request): swap colour tokens only; check contrast in both modes.

## 4. WordPress

Write for PHP 8.2+. Never edit core, a parent theme or third-party plugins; use a child theme or a site plugin.
- **Security (non-negotiable):** sanitize input, escape output late (`esc_html`, `esc_attr`, `esc_url`, `wp_kses_post`), nonces on every form/AJAX/REST action, `current_user_can` before privileged actions, REST routes with a real `permission_callback`, `$wpdb->prepare()` for every variable query.
- Hooks, not hacks; WP APIs over custom equivalents; cache expensive queries (transients/object cache).
- Prefix everything with the project slug or use namespaces; WPCS via PHPCS; `functions.php` only includes files from `/inc`.
- Enqueue properly on the right hook, versioned (`*.asset.php` or `filemtime()` in dev), `'strategy' => 'defer'`; no hard-coded `<script>`/`<link>`.
- Content structures (CPTs, taxonomies, fields, integrations) in a site plugin so they survive a theme change.
- Everything translatable with the text domain; editors change content in the editor, not code; remove unused bloat (emoji script, unused patterns).
- Local dev with Lando (`.lando.yml` in the repo) unless the project already uses another setup.

**Block themes:** `theme.json` v3 as the token source; patterns in `/patterns`; `block.json` `apiVersion: 3`; dynamic blocks with `render.php`; Interactivity API for front-end behaviour; core blocks + patterns + Block Bindings before custom blocks.

**Elementor + ACF:**
- Use Elementor Site Settings (global colours, fonts, breakpoints) as the token source; no per-widget hard-coded styles.
- Custom widgets: extend `\Elementor\Widget_Base`, register on `elementor/widgets/register`, escape in `render()`, load assets only via `get_script_depends()` / `get_style_depends()`.
- Dynamic data: prefer Elementor Dynamic Tags with ACF over custom shortcodes.
- ACF: register field groups in code or sync with Local JSON (`acf-json/` in the theme, committed to Git). `get_field()` returns raw data — escape it; `the_field()` escapes since ACF 6.2.7; for WYSIWYG use `get_field( $name, false, true, true )` or `wp_kses_post()`.
- Keep the plugin count lean; justify each plugin in the README.

**WooCommerce:** hooks and template overrides in the child theme with the template version header kept current; HPOS-compatible order access (`wc_get_order()`, never post meta directly).

## 5. Shopify

- Online Store 2.0: sections and blocks with complete `{% schema %}` so merchants edit in the theme editor; JSON templates; no hard-coded content.
- Data from metafields and metaobjects with definitions (typed), not tags or hard-coded lists.
- Validate Liquid with Theme Check (Shopify Dev MCP or `shopify theme check`) before calling work done.
- Work on a duplicate/unpublished theme via `shopify theme dev`; never edit the live theme directly.
- Assets: `image_url` + `image_tag` with widths/sizes; defer JS; minimal app embeds.
- Migrations: map products, variants, metafields, redirects (old URLs → `/products/…`) and customers before importing; verify counts after.

## 6. nopCommerce plugins

- Structure: `Nop.Plugin.{Group}.{Name}` project; `plugin.json` with Group, FriendlyName, SystemName (unique), Version, SupportedVersions (must include the running version or the plugin won't load), Author, DisplayOrder, FileName, Description.
- Plugin class extends `BasePlugin` and implements the right interface (`IWidgetPlugin`, `IPaymentMethod`, `IMiscPlugin`…); override `InstallAsync`/`UninstallAsync` and clean up settings, locales and tables on uninstall.
- Services registered in a `INopStartup` class; data access through repositories; schema changes as migrations.
- Views via view components; localisation through resource strings, never hard-coded text.
- Never modify nopCommerce core; extend through events, plugins and DI overrides. Check APIs for the exact version in the official docs.

## 7. React + Vite + TypeScript + Tailwind

- Strict TypeScript; typed props; no `any` without a comment; one component per file, `PascalCase.tsx`.
- State close to where it's used; derive instead of duplicating; URL state for filters and tabs.
- Every async view has loading, empty and error states.
- Tailwind v4 with `@theme` tokens; extract repeated utility groups into components, not `@apply` everywhere.
- Code-split routes; check bundle size before adding a dependency; Vitest for logic, Playwright for flows.
- Secrets never in client code (`VITE_` vars are public); `.env.example` committed.

## 8. Code quality (all projects)

- HTML: semantic landmarks, one `main`; buttons for actions, links for navigation, never a clickable `div`; native `<dialog>`, `<details>`, `popover` before custom widgets.
- CSS: no inline styles (except custom-property values); cascade layers (`reset, tokens, base, layout, components, utilities`); low specificity with `:where()`; logical properties; no `!important` except third-party overrides, with a comment; no IDs for styling; one approach per project (BEM-ish or Tailwind, SCSS with `@use`).
- JS: ES modules, `const`, early returns, no jQuery in new code, progressive enhancement, `AbortController` to clean up listeners, explicit loading/empty/error states.
- Naming: `kebab-case` files, `PascalCase.tsx` components, `camelCase` JS, prefixed `snake_case` PHP functions per WPCS. Comments explain why. Extract on the third repetition, not the first.
- Prettier + ESLint (+ Stylelint) configured in the repo.

## 9. Quality floors (all projects)

- **Accessibility, WCAG 2.2 AA:** contrast 4.5:1 text / 3:1 large text and UI, in every theme; meaningful `alt` (decorative `alt=""`); one `h1`, no skipped levels; full keyboard use, no traps, `Esc` closes overlays, focus moves into and back out of dialogs; visible `:focus-visible`, never hidden behind sticky headers (`scroll-padding-top`); targets ≥ 24×24px (44 on touch); visible labels and text errors linked with `aria-describedby`; skip link, `lang` on `<html>`, meaningful link text; native elements before ARIA.
- **Performance, Core Web Vitals "good":** LCP ≤ 2.5s, INP ≤ 200ms, CLS ≤ 0.1; Lighthouse mobile ≥ 90 where the platform allows. Modern image formats with sizes and dimensions; LCP image not lazy, `fetchpriority="high"`; self-hosted WOFF2, `font-display: swap`; minimal, deferred JS; reserve space for late content.
- **SEO:** unique title (~50–60 chars) and description (~150–160), clean lowercase URLs (WP permalinks `/%postname%/`), canonical, Open Graph, one `h1`, valid JSON-LD that matches visible content, sitemap, sane robots, noindex on staging.
- **Security:** no secrets in code or Git; validate on the server; escape output; HTTPS and security headers where the host allows; `npm audit` / `composer audit` / `dotnet list package --vulnerable`; least privilege.
- **Git:** small Conventional Commits (`feat:`, `fix:`…), branches per feature, PRs into `main`. Never commit `.env`, `wp-config.php`, uploads or credentials.

## 10. Definition of Done

Report each item; fix failures before saying it's done.
- [ ] Design direction visible; tokens only; checked with screenshots at 375 / 768 / 1280px, no horizontal scroll
- [ ] Critique pass done (Impeccable `critique` if installed, otherwise a written self-review against §3)
- [ ] No console errors; linters pass (ESLint / PHPCS / Theme Check / build warnings)
- [ ] Keyboard walkthrough works; A11y Enforcer check passes
- [ ] Perf Profiler / Lighthouse within targets, or the platform limit explained
- [ ] Code rules met (§8); platform rules met (§4–§7): escaping and nonces, editable in the editor, no core edits
- [ ] No secrets committed; README or `CLAUDE.md` updated for anything a future session needs
