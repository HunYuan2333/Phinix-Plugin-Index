# Package Catalog Data / 包元数据目录

This directory stores approved package candidate records for the Phinix Plugin Index.

本目录存储经审核准入的 Phinix 插件候选元数据记录。

---

## Directory Layout / 目录结构

Packages are grouped by the SHA-256 hash of their package ID:

文件按包 ID 的 SHA-256 哈希值分目录存放：

```text
packages/
└── <PACKAGE_ID_HASH>/
    └── <CANDIDATE_HASH>.json
```

- **`<PACKAGE_ID_HASH>`**: `sha256(package.id)` — groups all approved versions of a given package.
- **`<CANDIDATE_HASH>.json`**: `sha256(canonical_candidate_json)` — the exact candidate metadata file corresponding to an approved version.

---

## Metadata Schema / 元数据规范

Each package file implements the schema-v3 specification (`https://phinix.net/schemas/plugin-package-manifest/v3`):

每个元数据文件遵循 schema-v3 规范：

- **`id`**: Unique package identifier (e.g., `phinix.example.basic`).
- **`manifest`**: Declared version, dependencies, assembly bindings, and target Phinix version range.
- **`artifact`**: Fixed GitHub release URL, asset ID, asset name, byte size, and package SHA-256.
- **`localization`**: In-catalog localized display names, descriptions, and version change notes.
- **`state`**: Current lifecycle state (`active`, `deprecated`, etc.).

Package candidate files in this directory are immutable once merged. They are verified against cryptographically locked approval receipts in `label-approvals/` and `published/`.

本目录下的候选记录一经合入即不可变，并通过 `label-approvals/` 与 `published/` 中的加密锁进行一致性验证。
