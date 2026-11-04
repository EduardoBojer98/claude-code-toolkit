---
name: web-dev-standards
description: Personal web design and development standards and routing for this user's client work - design direction, accessibility, performance, security, Definition of Done, and stack rules for WordPress (CodeMate starter with SCF sections, block themes, Elementor, ACF, WooCommerce), Shopify (Liquid, metafields, metaobjects), nopCommerce (.NET plugins), React + Vite + TypeScript + Tailwind, and plain HTML/CSS/JS. Use when building, designing, fixing or reviewing a website, theme, plugin, store or web app.
---

# Web Dev Standards

_Version 2.4 · 2026-11-04 (last reviewed 2026-11-04) · Source of truth: github.com/EduardoBojer98/claude-setup_

Apply by default. When a project has its own conventions or a `CLAUDE.md`/`AGENTS.md`, follow them for
style and naming, but never go below the floors in §3.

## 1. How to work

- **Read first:** the project's `CLAUDE.md`/`AGENTS.md`, then only the files the task touches. Search for symbols before opening whole files.
- **Load only the reference the stack needs** (table in §2). Don't load the others.
- **Size the effort:**
  - Small edit → do it, verify it, report in a line. No plan, no extra skills.
  - Feature → read the relevant code, check docs once, build the smallest reliable solution, run related tests, report.
  - Migration, security work, unfamiliar system → short written plan, change in steps, test each step.
- **Docs:** check APIs with Context7 before using them; don't trust memory. Use these IDs directly (no lookup):
  Elementor `/elementor/elementor-developers-docs` ·
  ACF `/websites/advancedcustomfields_resources` · nopCommerce `/nopsolutions/nopcommerce-docs`.
  Shopify → the Shopify Dev MCP when available. Reuse what was looked up earlier in the session.
- **Helpers:** in Claude Code follow the global routing (cheap agents for search, test runs and doc lookups);
  elsewhere no helper agents unless the task splits into independent parts. No new dependency without a reason.
- **Never claim** a test passed, a page renders or a deploy worked without having run or seen it.
- **No vendor promotion** (tool or SaaS plugs) in client-facing output.
- Respect the platform: no React patterns in WordPress/Shopify, no Next.js advice in Vite apps, no new framework in an existing project.

## 2. Routing — load only what the project needs

| Signal | Read | Don't use |
|---|---|---|
| `AGENTS.md` naming the CodeMate starter, `template-parts/sections/`, `inc/features/` | [wordpress.md](references/wordpress.md) → CodeMate starter; the repo's `AGENTS.md` and `.claude/skills` rule | Block-theme and Elementor rules, `theme.json` |
| `theme.json`, `block.json`, custom WP plugin, WooCommerce code | [wordpress.md](references/wordpress.md) + matching WordPress Dev Skills skill | Shopify/React rules |
| Elementor active, ACF field groups, classic theme | [wordpress.md](references/wordpress.md) → Elementor + ACF | Block-theme defaults, WP.org/Freemius skills |
| `.liquid`, `config/settings_schema.json`, `shopify.theme.toml` | [shopify.md](references/shopify.md) + Shopify Dev MCP | WordPress skills |
| `*.csproj`, `plugin.json` with `SystemName` | [nopcommerce.md](references/nopcommerce.md) | Front-end design skills unless views change |
| `vite.config.*`, `tsconfig.json`, React | [react.md](references/react.md) + project's react-best-practices skill | WordPress skills |
| New page, section, redesign, or any HTML/CSS/JS | [design-and-code.md](references/design-and-code.md); Claude Code: `/impeccable craft` (turn on per project: `enable-plugins.sh design`); claude.ai: `frontend-design` | More than one design skill at once |
| Animation, scroll effects, page transitions | design-and-code.md → Motion (CSS first); GSAP skills only if the project already uses GSAP (`enable-plugins.sh motion`) | Adding GSAP/Motion to a project for a fade |
| UI work about to be called done | §4 review: `/impeccable critique` → `polish`, A11y Enforcer, Perf Profiler, Playwright | — |
| Before deploy or merging client work | `security-scan` in the project (secrets, dependencies, code patterns, WP plugins), then `/security-review`; fix or explain each finding | Paid scanners, `npm audit` + `composer audit` on top (OSV covers both) |
| A live site to look at, no code | Built-in browser; Chrome only for signed-in client admin | Playwright |
| Scripted screenshots, E2E, visual diffs | Playwright | Chrome extension |
| Something broken or failing | the `debug` skill (Claude Code) | Guess-and-patch |

## 3. Quality floors (all projects)

- **Accessibility, WCAG 2.2 AA:** contrast 4.5:1 text / 3:1 large text and UI, in every theme; meaningful `alt` (decorative `alt=""`); one `h1`, no skipped levels; full keyboard use, no traps, `Esc` closes overlays, focus moves into and back out of dialogs; visible `:focus-visible`, never hidden behind sticky headers (`scroll-padding-top`); targets ≥ 24×24px (44 on touch); visible labels and text errors linked with `aria-describedby`; skip link, `lang` on `<html>`, meaningful link text; native elements before ARIA.
- **Performance, Core Web Vitals "good":** LCP ≤ 2.5s, INP ≤ 200ms, CLS ≤ 0.1; Lighthouse mobile ≥ 90 where the platform allows. Modern image formats with sizes and dimensions; LCP image not lazy, `fetchpriority="high"`; self-hosted WOFF2, `font-display: swap`; minimal, deferred JS; reserve space for late content.
- **SEO:** unique title (~50–60 chars) and description (~150–160), clean lowercase URLs (WP permalinks `/%postname%/`), canonical, Open Graph, one `h1`, valid JSON-LD that matches visible content, sitemap, sane robots, noindex on staging.
- **Security:** no secrets in code or Git; validate on the server; escape output; HTTPS and security headers where the host allows; `security-scan` before deploy (gitleaks, OSV-Scanner for npm/Composer, Semgrep, WordPress plugin advisories), `dotnet list package --vulnerable` for .NET; least privilege; WordPress: nonces + capability checks on every action, `$wpdb->prepare`, sanitize in / escape out.
- **Git:** small Conventional Commits (`feat:`, `fix:`…), branches per feature, PRs into `main`. Never commit `.env`, `wp-config.php`, uploads or credentials.

## 4. Definition of Done

Report each item that applies; fix failures before saying it's done.
- [ ] Design direction visible; tokens only; checked with screenshots at 375 / 768 / 1280px, no horizontal scroll
- [ ] Critique pass done (`/impeccable critique` in Claude Code; on claude.ai a written self-review against the Design section of design-and-code.md)
- [ ] Motion: `prefers-reduced-motion` respected, only `transform`/`opacity` animated, no layout shift
- [ ] No console errors; linters pass (ESLint / PHPCS / Theme Check / build warnings)
- [ ] Keyboard walkthrough works; A11y Enforcer check passes
- [ ] Perf Profiler / Lighthouse within targets, or the platform limit explained
- [ ] Code rules met (design-and-code.md); platform rules met (stack reference): escaping and nonces, editable in the editor, no core edits
- [ ] `security-scan` clean (or each finding explained) and `/security-review` run on the diff before deploy
- [ ] No secrets committed; README or `CLAUDE.md` updated for anything a future session needs
