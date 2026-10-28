# Stack diagnostics

Read only the section you need. Commands assume the project root.

## WordPress on Lando
- State: `lando info` (services, URLs, DB creds), `lando list`. Rebuild only if config changed: `lando rebuild -y` (ask first: it recreates containers).
- Logs: `lando logs -s appserver --follow` (Ctrl-C), PHP errors with `WP_DEBUG_LOG` → `wp-content/debug.log`.
  Enable temporarily: `lando wp config set WP_DEBUG true --raw && lando wp config set WP_DEBUG_LOG true --raw` (revert afterwards).
- WP-CLI inside Lando: `lando wp plugin list --status=active`, `lando wp option get siteurl`,
  `lando wp cron event list`, `lando wp rewrite flush`, `lando wp cache flush`.
- Isolate plugins/theme: `lando wp plugin deactivate --all --skip-plugins` on a DB backup only
  (`lando db-export backup.sql.gz` first), or `--skip-plugins=<slug>` / `--skip-themes` per command.
- Hooks: find who adds a callback with `rg "add_(action|filter)\(\s*'hook_name'"`; priority bugs are common.
- ACF/SCF: `acf-json/` out of sync → field group "Sync available" in admin; never rename field `name`/`key`.
- White screen / 500: check `debug.log`, then `lando logs -s appserver`; PHP version mismatch → `.lando.yml` `php:`.
- Lando itself: `lando version`, `docker ps`, port conflicts (`ss -ltnp | rg ':80|:443'`), `lando poweroff` then `lando start`.

## Shopify themes
- `shopify theme check` (or Shopify Dev MCP validation) for Liquid/schema errors; fix errors before warnings.
- `shopify theme dev --store <store>` on an unpublished theme; never debug on the live theme.
- Liquid: `{{ variable | json }}` to inspect objects (remove after). Missing data → check metafield definitions/namespaces and template JSON block settings.
- JSON templates: invalid section/block `type` or removed setting ids break the editor; compare with `{% schema %}`.
- Storefront JS: browser console + Network tab; section rendering API responses for AJAX carts.

## React + Vite + TypeScript
- Type errors: `npx tsc --noEmit -p .` (or the repo's `typecheck` script).
- Build vs dev differences: `npm run build && npm run preview`; env vars must be `VITE_` prefixed.
- Render loops / stale state: check effect dependency arrays and derived state; React DevTools Profiler for slow renders.
- Tests: `npx vitest run <file>`; Playwright flows: `npx playwright test <spec> --reporter=line`.

## Node / APIs
- Reproduce the request with `curl -sS -i` (no secrets in the command line; read them from env).
- Check runtime version vs `.nvmrc`/`engines`; `node --trace-warnings` for warnings; `npm ls <pkg>` for duplicate versions.

## CI (GitHub Actions)
- `gh run list -L 5`, `gh run view <id> --log-failed | tail -n 150`.
- Compare CI versions (PHP/Node/OS) with local before changing code.

## Performance
- Front end: Perf Profiler / Lighthouse on the specific URL; check LCP element, render-blocking assets, layout shifts.
- WordPress: Query Monitor plugin (local only), slow queries, autoloaded options size (`lando wp option list --autoload=on --format=count`).
