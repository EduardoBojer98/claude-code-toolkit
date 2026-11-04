# WordPress

Part of web-dev-standards. Load for any WordPress, WooCommerce, ACF/SCF or Elementor work.

Write for PHP 8.3+ (PHP 8.2 security support ends 31 Dec 2026; WordPress recommends 8.3+). Target the current WordPress release (7.1) and test against the next one before it ships. Never edit core, a parent theme or third-party plugins; use a child theme or a site plugin.
- **Security (non-negotiable):** sanitize input, escape output late (`esc_html`, `esc_attr`, `esc_url`, `wp_kses_post`), nonces on every form/AJAX/REST action, `current_user_can` before privileged actions, REST routes with a real `permission_callback`, `$wpdb->prepare()` for every variable query.
- Hooks, not hacks; WP APIs over custom equivalents; cache expensive queries (transients/object cache).
- Prefix everything with the project slug or use namespaces; WPCS via PHPCS; `functions.php` only includes files from `/inc`.
- Enqueue properly on the right hook, versioned (`*.asset.php` or `filemtime()` in dev), `'strategy' => 'defer'`; no hard-coded `<script>`/`<link>`.
- Content structures (CPTs, taxonomies, fields, integrations) in a site plugin so they survive a theme change.
- Everything translatable with the text domain; editors change content in the editor, not code; remove unused bloat (emoji script, unused patterns).
- Local dev with Lando (`.lando.yml` in the repo) unless the project already uses another setup.

**New WordPress client sites start from the CodeMate starter** (github.com/EduardoBojer98/wordpress-starter). Its `AGENTS.md`, `docs/` and ADR 0001 rule there and win over the rest of this section; the quality floors in SKILL.md still apply. In short:
- Classic theme, block editor off everywhere; pages are built only from SCF "Page sections" (one form per section; folder `template-parts/sections/<name>/` + `acf-json/group_st_section_<name>.json`); posts use the classic editor; site facts live in Website Settings.
- **Secure Custom Fields is required; never install ACF alongside it.** Never rename a field `name`/`key` once content exists.
- Tokens: `assets/scss/abstracts/_palettes.scss` (colours, light + dark) and `_variables.scss`, output as `--color-*` custom properties; no `theme.json`. Section CSS in `@layer sections`, loaded only where the section is used.
- Prettier formats everything (PHP included); PHPCS checks security and WordPress API use; PHPStan level 5. Run PHP/WP-CLI inside Lando; back up the DB before migrations or bulk changes.
- Use the repo's project skills (`start-project`, `add-section`, `add-feature`) and fill `docs/project/` per client.

**Block themes** (only when a project needs the Site Editor or native blocks): `theme.json` v3 as the token source; patterns in `/patterns`; `block.json` `apiVersion: 3`; dynamic blocks with `render.php`; Interactivity API for front-end behaviour; core blocks + patterns + Block Bindings before custom blocks. WP 7.1+: responsive styles via `theme.json` `settings.viewport` and `@mobile`/`@tablet`, before custom media-query CSS. The post editor is always iframed: editor scripts and styles must target the canvas document, not the admin `document`.

**Elementor + ACF** (existing client sites built that way; Elementor 4 Atomic Editor is the default on new installs, existing sites stay on their current editor unless the client opts in):
- Use Elementor Site Settings (global colours, fonts, breakpoints) as the token source; no per-widget hard-coded styles.
- Custom widgets: extend `\Elementor\Widget_Base`, register on `elementor/widgets/register`, escape in `render()`, load assets only via `get_script_depends()` / `get_style_depends()`.
- Dynamic data: prefer Elementor Dynamic Tags with ACF over custom shortcodes.
- ACF: register field groups in code or sync with Local JSON (`acf-json/` in the theme, committed to Git). `get_field()` returns raw data — escape it; `the_field()` escapes since ACF 6.2.7; for WYSIWYG use `get_field( $name, false, true, true )` or `wp_kses_post()`. New ACF blocks use Blocks V3 (`"blockVersion": 3` in `block.json`; the default on WP 7.1+ since ACF 6.8.9). Keep SCF/ACF on the latest security release.
- Keep the plugin count lean; justify each plugin in the README.

**WooCommerce:** hooks and template overrides in the child theme with the template version header kept current; HPOS-compatible order access (`wc_get_order()`, never post meta directly).

