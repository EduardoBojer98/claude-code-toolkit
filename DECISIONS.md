# Decisions

Why each tool is in, out or skipped. Every review reads this first and updates it last.
Free-only rule applies to everything (see MAINTENANCE.md).

## In (enabled)
| Tool | Kind | Why | Added | Re-check |
|---|---|---|---|---|
| web-dev-standards | Own skill | Design, code, WP, a11y, perf, SEO, security standards + Definition of Done | 2026-10-16 | every review |
| toolkit-maintainer | Own skill | Runs these reviews | 2026-10-16 | every review |
| frontend-design | Plugin (Anthropic) | Distinctive design direction; user designs in code | 2026-10-16 | — |
| WordPress Dev Skills | Plugin (community) | WPCS/PHPCS, @wordpress/scripts, WooCommerce, testing, i18n | 2026-10-16 | maintenance activity |
| github | Plugin (GitHub, partner) | Repos, issues, PRs; free account, OAuth | 2026-10-16 | — |
| playwright | Plugin (Microsoft, partner) | Visual checks at breakpoints, E2E tests; local, open source | 2026-10-16 | — |
| A11y Enforcer | Plugin (community) | WCAG 2.2 checks and fixes; markdown-only | 2026-10-16 | maintenance activity |
| Perf Profiler | Plugin (community) | Lighthouse / Core Web Vitals diagnosis; markdown-only | 2026-10-16 | maintenance activity |
| searchfit-seo | Plugin | Meta, schema, technical SEO; markdown-only | before 2026-10-16 | — |
| Context7 | Connector | Current docs for WP, Next.js, React, Tailwind | 2026-10-16 | **free tier (watchlist)** |
| figma | Plugin + connector | Optional; user designs in code | before 2026-10-16 | removal candidate if unused |
| caveman | Plugin | Optional, not web-dev | before 2026-10-16 | removal candidate |

## Nice to have (not installed)
| Tool | Why not yet |
|---|---|
| WordPress DevKit | Overlaps WordPress Dev Skills; adds auto-running hooks. Revisit if block scaffolding is needed. |
| code-review (Anthropic) | Useful for PR review once GitHub workflow is in daily use |
| Skills for React/React Native Engineers | Next.js/Tailwind/GSAP skills; heavy mobile content |
| finecomb | Deep security audit checklist for client handoffs |
| Netlify connector | Free plan: 300 credits/month hard cap. Only if a client hosts there. |
| CI Optimizer | Once GitHub Actions are used |

## Skip
| Tool | Reason | Checked |
|---|---|---|
| Axe Accessibility (Deque) | Needs paid axe DevTools subscription via sales | 2026-10-16 |
| Bright Data | Needs account + API key; free tier not confirmed card-free; overrides web search | 2026-10-16 |
| Vercel connector | Hobby plan bans commercial use; Pro $20/seat/month for client work | 2026-10-16 |
| ThemeSniffer | External service, pricing unconfirmed | 2026-10-16 |
| WordPress.com plugin/connector | Only for WordPress.com-hosted sites | 2026-10-16 |
| Lovable, Replit, Macaly, Railway, Render | Paid hosting/app-builder platforms, not needed | 2026-10-16 |
| Linear, Notion | Not used by the user | 2026-10-16 |
| Kobiton, PactFlow | Not relevant | 2026-10-16 |

## Pricing watchlist
Re-verify every review; these have changed before or are close to the line.
| Tool | Current free terms | Source | Checked |
|---|---|---|---|
| Context7 | 1,000 requests/month (cut from ~200/day in Jan 2026), needs free account | blog.devgenius.io Context7 free-tier article | 2026-10-16 |
| Netlify | 300 credits/month, sites pause when exhausted | netli.fyi free plan limits 2026 | 2026-10-16 |
| Vercel Hobby | Free but non-commercial | deploywise.dev free tier limits 2026 | 2026-10-16 |
| PageSpeed Insights API | Free with a free Google API key | unlighthouse.dev | 2026-10-16 |
