# Shopify

Part of web-dev-standards. Load for Liquid themes, metafields/metaobjects and store migrations.

- Online Store 2.0: sections and blocks with complete `{% schema %}` so merchants edit in the theme editor; JSON templates; no hard-coded content.
- Data from metafields and metaobjects with definitions (typed), not tags or hard-coded lists.
- Validate Liquid with Theme Check (Shopify Dev MCP or `shopify theme check`) before calling work done.
- Work on a duplicate/unpublished theme via `shopify theme dev`; never edit the live theme directly.
- Assets: `image_url` + `image_tag` with widths/sizes; defer JS; minimal app embeds.
- Migrations: map products, variants, metafields, redirects (old URLs → `/products/…`) and customers before importing; verify counts after.

