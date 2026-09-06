# Loadout Builder

The Equipment section is isolated in website/loadout. Existing Twitch, Hangar,
vehicle pages and Cloudflare APIs are unchanged. The original equipment catalogue
remains available under Full catalogue.

## Modules
- index.js: bilingual UI, lazy loading, catalogue pagination, comparison,
  shop offers, mobile panels, JSON/image export and share links.
- core.js: slot compatibility, build validation, nominal metrics and suggestions.
- storage.js: versioned local storage adapter (50 builds maximum).
- data/catalog.json: generated, pinned snapshot, not a runtime external API.
- loadout.css: scoped dark/cyan styling.

## Data refresh
Source: StarCitizenWiki/scunpacked-data at
f6a2b29e77aaa2c824aa4fd1c0478c8058c69fca (4.10.0-LIVE.12519617).
Download ships.json and ship-items.json from that revision, then run:

    node scripts/build-loadout-data.mjs <ships.json> <ship-items.json>
    node tests/loadout.mjs

Node with node:sqlite support is required. Prices use exact component UUID joins
against data/asteriax_sc.db. Missing prices stay unknown, never zero.
To upgrade the patch, update generator provenance as well as source inputs.
The snapshot does not update automatically.

## Boundaries
Stock mounts/racks remain fixed. Compatibility uses slot sizes, types, subtypes
and required tags. Metrics are nominal, include turret weapons and do not simulate
capacitors, crew, full resource networks or combat. Suggestions are per-slot
heuristics, not globally optimal PvE/PvP simulations.
Technical and shop datasets may refer to different patches; the UI discloses this.

Builds currently live on the device, not in the Twitch/Hangar account.
A future account adapter can replace storage.js without changing compatibility.
Shared builds include patch and slot identifiers, and are validated before use.
Imports from a different patch are rejected rather than silently migrated.

## Verification
Run node tests/loadout.mjs and node --check website/loadout/index.js.
For local UI checks run node tests/serve-loadout.cjs. The normal Pages build
copies database/assets; API endpoints are not emulated by this static test server.
