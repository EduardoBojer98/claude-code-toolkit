# Changelog

## 2026-10-22: Claude Code review (WSL)
- Figma kept in Claude Code (62 uses of design-to-code in 20 days); ponytail kept by preference; hyperframes and mattpocock-skills disabled.
- 13 claude.ai-synced skills unused in Claude Code disabled per machine (~2,370 tokens a turn); duplicate user-level copies of own skills disabled.

## 2026-10-22: caveman restored
- Re-enabled by user preference; snapshot moved from `archive/plugins/` back to `plugins/`. Opt-in only ("caveman mode").

## 2026-10-22: web-dev-standards 2.1
- WordPress client sites start from the CodeMate starter (classic theme, SCF page sections, runtime CSS tokens, Lando); its `AGENTS.md` and ADR 0001 rule there. Block themes only when the Site Editor or native blocks are needed; Elementor + ACF rules apply to existing sites built that way.
- Replaces PR #1 (written against v1.0, which v2.0 replaced); its intent is carried over in full.

## 2026-10-22: lean design + engineering setup
- Added `archive/` (never deleted): VectorLab UI/UX Skills (first backup; it had been enabled outside a review), frontend-design plugin copy, caveman, figma, github; v1.0 of both own skills; the monthly task prompt. All copies verified identical to the live versions.
- `scripts/refresh-snapshot.sh` now moves snapshots of no-longer-enabled plugins to `archive/plugins/` instead of deleting them.
- `web-dev-standards` v2.0: routing per stack (WordPress/Elementor/ACF, Shopify, nopCommerce, React+Vite), working rules, pinned Context7 IDs; 1,817 words (v1.0: 2,620), all v1.0 rules kept in shorter form.
- `toolkit-maintainer` v1.1: free-first (paid only with strong evidence), archive-never-delete rule, new stack keywords.
- Added `templates/CLAUDE.md` for client projects.
- Adopted in Claude Code: Shopify Dev MCP; Impeccable (trial); Vercel react-best-practices per React project.

## 2026-10-16: initial setup
- Added own skills: `web-dev-standards` v1.0, `toolkit-maintainer` v1.0
- Installed: WordPress Dev Skills, github, playwright, A11y Enforcer, Perf Profiler; connector Context7
- Kept: frontend-design, searchfit-seo, figma, caveman
- Disabled: brightdata-plugin (needs paid account/API key)
- Created this backup repo with plugin snapshot, manifest, decisions log and monthly review process
