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

## Third-party authors and distribution

Author repositories may belong to any public GitHub user or organization. The
`artifact` record always identifies the author's original repository, owner,
source commit, release, asset and approved bytes; there is no first-party owner
allowlist. Maintainers review the record and redistribution permission/license
before merging it. An author can propose the record through a pull request; only
maintainers can dispatch publication. This is reviewed admission, not automatic
approval or automatic upstream updating.

Publication revalidates every active author's ZIP with the actual theme reader.
It then saves a byte-identical copy in the same controlled Release as catalog.json,
named `theme-<approved ZIP SHA256>.zip`. Identical bytes are deduplicated by hash.
All stored bytes are downloaded and reverified before the Release is published
and the stable pointer advances. A public Release is never repaired or clobbered
in place; missing/conflicting assets require a new reviewed snapshot. Withdrawn
records are not distributed.

CF serves these verified distribution copies using the existing Index credential.
It never needs an author's token or an organization-specific secret. GitHub direct
continues using the original author asset. Both routes return exactly the same
approved ZIP and the client still verifies its digest/manifest/XML. The schema4
record format and installed theme provenance stay unchanged.

This persistent Release mirror is distinct from Cloudflare caching. Production CF
currently caches metadata briefly and streams ZIPs; R2/edge ZIP caching is disabled.
The existing verified-stream cache layer can accept third-party themes by immutable
source/package/version/hash, but enabling that production storage requires its
separate cache rollout checks. Older pre-mirror snapshots cannot gain mirrors in
place; clients must refresh to a newly published snapshot to use CF mirror delivery.
