# Decisions

Why each tool is in, archived, watched or skipped. Every review reads this first and updates it last.
Free first; paid only with strong evidence (see MAINTENANCE.md). Retired tools are archived, never deleted (see `archive/README.md`).

## In (enabled)
| Tool | Kind | Role | Why | Added | Re-check |
|---|---|---|---|---|---|
| web-dev-standards v2.1 | Own skill | Core | Standards, routing per stack (incl. CodeMate starter), Definition of Done | 2026-10-16 (v2.1 2026-10-22) | every review |
| toolkit-maintainer v1.1 | Own skill | Maintenance | Runs reviews, archives retired tools | 2026-10-16 (v1.1 2026-10-22) | every review |
| frontend-design (built-in) | Built-in skill | Core | Visual direction on new pages | built-in | — |
| Context7 | Connector | Core | Current docs; pinned IDs for Elementor, ACF, nopCommerce | 2026-10-16 | **free tier (watchlist)** |
| playwright | Plugin (Microsoft) | Review | Screenshots at 375/768/1280, E2E; runs `@latest` (pin if a release breaks) | 2026-10-16 | release notes |
| A11y Enforcer | Plugin (community) | Review | WCAG 2.2 scan + contrast; local scripts | 2026-10-16 | maintenance activity |
| Perf Profiler | Plugin (community) | Review | Lighthouse / PSI analysis; local scripts | 2026-10-16 | maintenance activity |
| WordPress Dev Skills | Plugin (community) | Conditional | WP plugin / WooCommerce / PHPCS / testing depth | 2026-10-16 | maintenance activity |
| caveman | Plugin (community) | Optional | Terse replies on request ("caveman mode"); kept by user preference, restored 2026-10-22. Only active when asked for | 2026-10-22 | — |
| searchfit-seo | Plugin | Optional | SEO audits and schema; ignore its SearchFit.ai promotion lines | before 2026-10-16 | — |

## Built 2026-10-22: free-model fallback (ccfb, `fallback/`)
| Choice | Decision | Why |
|---|---|---|
| Approach | Local gateway via `ANTHROPIC_BASE_URL`; Claude passthrough, fallback only on plan-limit 429 | Documented subscription pass-through; same session continues; see fallback/DESIGN.md |
| Implementation | Python standard library only | No dependencies to install or be compromised (the gateway sees the claude.ai token) |
| Providers on by default | OpenRouter free models, Gemini free tier | Free, tool calling, large context; keys from the user |
| Off by default | Cerebras (trial only), Ollama (local, opt-in) | Trial is not a permanent free tier; local depends on hardware |
| Rejected | Groq (8K TPM free < one Claude Code request), LiteLLM (heavy; March 2026 PyPI compromise), claude-code-router as core (no plan-limit fallback/pass-through) | See DESIGN.md "Existing tools considered" |

## Adopted 2026-10-22 (installed by the user in Claude Code)
| Tool | Kind | Role | Why | Condition |
|---|---|---|---|---|
| Shopify Dev MCP (`@shopify/dev-mcp@1.17.0`, WSL user scope, connected) | Local MCP, official, free | Conditional (Shopify) | Liquid docs, Theme Check validation, Admin GraphQL schema | Pinned version |
| Impeccable (pbakaus/impeccable, Apache 2.0) | Claude Code plugin | Review (design critique/polish) | Builds on frontend-design; adds critique, audit, polish and 61 detector rules | Telemetry off; removed if it doesn't beat frontend-design alone on the benchmark |
| Vercel react-best-practices | Project skill | Conditional (React repos only) | React performance rules | Installed per project in `.claude/skills/` |

## Claude Code (local machine), reviewed 2026-10-22 from its own usage stats
| Tool | Decision | Evidence |
|---|---|---|
| figma (claude-plugins-official) | **Keep in Claude Code**; re-authenticate its MCP | `figma-design-to-code` used 62× in 20 days: Figma designs are implemented in code. Still off on claude.ai (no use there) |
| ponytail (DietrichGebert/ponytail) | Keep (user's choice) | Code-minimalism rules injected each turn; matches web-dev-standards. Avoid `ultra` mode on client sites |
| hyperframes (heygen-com) | Disable | 21 skills, never used; HTML-to-video, not daily work |
| mattpocock-skills (claude-plugins-official) | Disable | 27 skills, one use (setup) in 9 days |
| claude.ai-synced built-in skills in Claude Code (built-in-browser, chrome-browser, computer-use, deep-research, docs, docx, google-workspace, import-memory, morning, pdf, pptx, skill-creator, xlsx) | Disable per machine in `/skills` | Never used in Claude Code; ~2,370 tokens of listings every turn (Claude Code's own estimate). Stay on for claude.ai |
| user-level copies of web-dev-standards / toolkit-maintainer | Disable in `/skills` | Duplicates of the claude.ai-synced `anthropic-skills:` versions |

## Archived 2026-10-22 (disabled, files in `archive/plugins/`)
| Tool | Why |
|---|---|
| VectorLab UI/UX Skills | Product-UI rules conflicting with web-dev-standards (WCAG 2.1, SaaS look, page-pattern lock); 4 useful microcopy rules moved into web-dev-standards §3 |
| frontend-design plugin | Identical to the built-in skill |
| figma (claude.ai plugin + connector) | Not used on claude.ai; the Claude Code install is kept (see above) |
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
