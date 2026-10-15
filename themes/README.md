# Data-only theme publication

Theme records are separate from the existing plugin catalog. Reviewed source records
live in `themes/packages/*.json` on main (schema1 envelope, `package` schema4 record).
A maintainer dispatches `Theme catalog publication` for that exact main commit.
The check-only default validates without writes; a second explicit dispatch publishes.
The workflow rechecks fixed public repository IDs, release/tag/asset membership,
ZIP/manifest/XML digests with the actual Common theme reader, and main/actor authority.

Published metadata lives at `stable.json` and `published/<snapshot>.json` on the
`themes` publication branch. Source ID: `phinix.themes`; catalog schema: 4.
Immutable catalogs use `theme-catalog-v4-<main-commit>` release tags. The existing
`phinix.official` main-branch plugin pointer is never modified by this workflow.
Previous package versions remain in the feed; only state may change. No automatic
upstream update approval is offered for themes in this first release.

Theme ZIPs contain no assemblies. Keep author source XML and package configuration
in the author repository; use a fixed public non-prerelease release. Install does
not apply a palette. Publish a supported Host first, then theme packages and records.
