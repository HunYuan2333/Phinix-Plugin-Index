# Dual-runtime package rollout

Catalog schema3 and immutable author asset routes stay unchanged. Package manifests may use schema2 variants (1.6/net472 and 1.7/net10.0) with one product identity/version. Python scripts preserve the envelope and project shared product facts; the trusted CLR validator must inspect both variants.

The working-tree implementation is tested locally. Production snapshots have been refreshed from actual Host afb6afb6c5f68b8815964ebab7092a1b033b682e and Common 9d0710aaa9b41c07f28d9bfa25599247e7bb1f93; all 15 frozen files match committed bytes. Further changes must refresh the trusted snapshot via scripts/validator_snapshot.py using exact matching origins. Do not write fictitious SHAs or snapshot dirty working trees. The pure ManagedExtensionZip.cs is added to the trusted inputs; installation partial code is deliberately excluded.

For local static validation only:

```sh
python3 scripts/build-current-validator.py \
  --client-root ../Phinix-Rework \
  --common-root ../Phinix-Rework/Dependencies/Phinix.Common \
  --output /tmp/phinix-index-local-validator
```

Output must be fresh and outside source trees. This never changes production provenance or executes candidate DLLs. Use its Validator.dll with scripts/catalog.py project/build to validate local candidates.

Single-profile/API2 to dual-profile/API3 is a new compatibility scope and requires fresh admission once. Subsequent patches within the approved profile/API ranges retain automatic updates. Runtime/profile/range changes are rejected by source-update policy.

Local checks: 119 tests passed (one existing skip), all three real dual ZIPs passed static DLL inspection and en-US/zh-CN projection. Historical frozen snapshot digest checks pass after restoring ManagedExtensionMetadata.cs from its exact recorded Common commit. No catalog/stable/releases/approval receipts were published or rewritten.
