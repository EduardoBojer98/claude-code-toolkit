# Decisions

Why each tool is in, archived, watched or skipped. Every review reads this first and updates it last.
Free first; paid only with strong evidence (see MAINTENANCE.md). Retired tools are archived, never deleted (see `archive/README.md`).

## In (enabled)
| Tool | Kind | Role | Why | Added | Re-check |
|---|---|---|---|---|---|
| web-dev-standards v2.0 | Own skill | Core | Standards, routing per stack, Definition of Done | 2026-10-16 (v2 2026-10-22) | every review |
| toolkit-maintainer v1.1 | Own skill | Maintenance | Runs reviews, archives retired tools | 2026-10-16 (v1.1 2026-10-22) | every review |
| frontend-design (built-in) | Built-in skill | Core | Visual direction on new pages | built-in | — |
| Context7 | Connector | Core | Current docs; pinned IDs for Elementor, ACF, nopCommerce | 2026-10-16 | **free tier (watchlist)** |
| playwright | Plugin (Microsoft) | Review | Screenshots at 375/768/1280, E2E; runs `@latest` (pin if a release breaks) | 2026-10-16 | release notes |
| A11y Enforcer | Plugin (community) | Review | WCAG 2.2 scan + contrast; local scripts | 2026-10-16 | maintenance activity |
| Perf Profiler | Plugin (community) | Review | Lighthouse / PSI analysis; local scripts | 2026-10-16 | maintenance activity |
| WordPress Dev Skills | Plugin (community) | Conditional | WP plugin / WooCommerce / PHPCS / testing depth | 2026-10-16 | maintenance activity |
| caveman | Plugin (community) | Optional | Terse replies on request ("caveman mode"); kept by user preference, restored 2026-10-22. Only active when asked for | 2026-10-22 | — |
| searchfit-seo | Plugin | Optional | SEO audits and schema; ignore its SearchFit.ai promotion lines | before 2026-10-16 | — |

## Adopted 2026-10-22 (installed by the user in Claude Code)
| Tool | Kind | Role | Why | Condition |
|---|---|---|---|---|
| Shopify Dev MCP (`@shopify/dev-mcp@1.17.0`, WSL user scope, connected) | Local MCP, official, free | Conditional (Shopify) | Liquid docs, Theme Check validation, Admin GraphQL schema | Pinned version |
| Impeccable (pbakaus/impeccable, Apache 2.0) | Claude Code plugin | Review (design critique/polish) | Builds on frontend-design; adds critique, audit, polish and 61 detector rules | Telemetry off; removed if it doesn't beat frontend-design alone on the benchmark |
| Vercel react-best-practices | Project skill | Conditional (React repos only) | React performance rules | Installed per project in `.claude/skills/` |

## Archived 2026-10-22 (disabled, files in `archive/plugins/`)
| Tool | Why |
|---|---|
| VectorLab UI/UX Skills | Product-UI rules conflicting with web-dev-standards (WCAG 2.1, SaaS look, page-pattern lock); 4 useful microcopy rules moved into web-dev-standards §3 |
| frontend-design plugin | Identical to the built-in skill |
| figma (plugin + connector) | Designs are made in code; Starter/View seat = 20 MCP reads/month |
| github plugin | Inactive (needs PAT); `gh` CLI covers it |

## Watchlist
| Tool | Status | Re-check |
|---|---|---|
| WordPress MCP Adapter (WordPress AI Team) | v0.7.0, pre-1.0; local WP-CLI stdio only if adopted | next review |
| Elementor MCP (official) | Beta since 2026-09-15; needs Atomic Editor | when out of beta |
| Taste Skill (Leonxlnx) | v2.1, MIT; overlaps frontend-design/Impeccable | if Impeccable is rejected |
| Vercel web-design-guidelines | Fetches rules from GitHub every run; overlaps Impeccable audit + A11y Enforcer | if Impeccable is rejected |

## Skip
| Tool | Reason | Checked |
|---|---|---|
| UI/UX Pro Max | Preset catalogue (styles/palettes) works against distinct direction; can't be uploaded to claude.ai (>200 files) | 2026-10-22 |
| nopStation MCP Server | Paid; store operations only; nopCommerce 4.90 only | 2026-10-22 |
| Axe Accessibility (Deque) | Needs paid axe DevTools subscription | 2026-10-16 |
| Bright Data | Needs account + API key | 2026-10-16 |
| Vercel connector | Hobby plan bans commercial use | 2026-10-16 |
| ThemeSniffer | External service, pricing unconfirmed | 2026-10-16 |
| WordPress.com plugin/connector | Only for WordPress.com-hosted sites | 2026-10-16 |
| Lovable, Replit, Macaly, Railway, Render | Paid platforms, not needed | 2026-10-16 |
| Linear, Notion | Not used | 2026-10-16 |
| Kobiton, PactFlow | Not relevant | 2026-10-16 |

## Pricing watchlist
| Tool | Current free terms | Source | Checked |
|---|---|---|---|
| Context7 | 1,000 requests/month, free account | blog.devgenius.io (Jan 2026) | 2026-10-22 |
| Figma MCP | View/Collab seats 20 reads/month; Full/Dev not on Starter | developers.figma.com rate limits | 2026-10-22 |
| Netlify | 300 credits/month | netli.fyi | 2026-10-16 |
| Vercel Hobby | Free but non-commercial | deploywise.dev | 2026-10-16 |
| PageSpeed Insights API | Free with a free Google API key | unlighthouse.dev | 2026-10-16 |
