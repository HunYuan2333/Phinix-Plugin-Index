# Review Records / 审核记录

This directory stores permanent, auditable review evidence generated during the package admission process.

本目录存储插件准入过程中生成的不可变审计与审核凭证。

---

## Directory Layout / 目录结构

```text
reviews/
└── <PACKAGE_ID_HASH>/
    └── <CANDIDATE_HASH>.json
```

- **`<PACKAGE_ID_HASH>`**: `sha256(package.id)` — groups review records for the package.
- **`<CANDIDATE_HASH>.json`**: Cryptographic review record binding the exact candidate version.

---

## Content & Proofs / 记录内容与证明

Each review record binds:
- The intake issue number and issue body fingerprint.
- The reviewer's identity and GitHub label event metadata.
- Automated static validation results and SHA-256 digests.
- Pinned source repository, commit SHA, and release asset information.

Review records are created automatically by the `plugin-label-admission.yml` workflow when a maintainer applies the `plugin-approved` label. No credentials, access tokens, or private personal data are stored in this directory.

审核记录在维护者打上 `plugin-approved` 标签后由 `plugin-label-admission.yml` 自动化工作流生成。本目录不保存任何私有凭证、访问密钥或私人隐私数据。
