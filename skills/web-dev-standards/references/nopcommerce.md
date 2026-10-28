# nopCommerce plugins

Part of web-dev-standards. Load for nopCommerce/.NET plugin work.

- Structure: `Nop.Plugin.{Group}.{Name}` project; `plugin.json` with Group, FriendlyName, SystemName (unique), Version, SupportedVersions (must include the running version or the plugin won't load), Author, DisplayOrder, FileName, Description.
- Plugin class extends `BasePlugin` and implements the right interface (`IWidgetPlugin`, `IPaymentMethod`, `IMiscPlugin`…); override `InstallAsync`/`UninstallAsync` and clean up settings, locales and tables on uninstall.
- Services registered in a `INopStartup` class; data access through repositories; schema changes as migrations.
- Views via view components; localisation through resource strings, never hard-coded text.
- Never modify nopCommerce core; extend through events, plugins and DI overrides. Check APIs for the exact version in the official docs.

