# GitHub index bot operations

[中文](GitHubBotGuide.zh-CN.md). 2026-10-05. Repository: [HunYuan2333/Phinix-Plugin-Index](https://github.com/HunYuan2333/Phinix-Plugin-Index).

Use GitHub Actions with `github-actions[bot]`. No server, GitHub App or new personal token is needed initially. Workflows use the repository-provided `GITHUB_TOKEN`, defaulting to read access; only the report job requests `issues: write`. The Cloudflare read-only origin token is separate and is never reused for index writes.

## A1: submission and static reports

Authors use Issues → New issue → Plugin submission. Copy [the example](examples/managed-submission.json) and replace every field with their fixed release, including public repository/owner IDs, source commit, published release/asset IDs, manifest, size and hashes. The real Playtest 1.2.1 example is test input, not an approved official entry. Titles start with `[Plugin]`; the form produces a `Candidate JSON` section.

New, edited or reopened submissions trigger strict client-equivalent schema-v2 validation, GitHub public repository/owner identities, non-draft/non-prerelease release, tag-to-commit proof, public C# source tree, asset membership/identity/size and actual SHA-256. Downloads use only GitHub API and the allowed asset CDN. Production ZIP/PE validation checks layout, manifest/content digests, target framework, assembly and module declarations without loading or executing plugin code.

Artifacts contain canonical `candidate.json`, `static.json` and `report.json`, binding the candidate fingerprint and issue body hash/update time. The issue is rechecked before completion and reporting; changed submissions stop stale reports. The bot posts pass/fail and fingerprint on an unchanged issue. Artifacts expire after 14 days; downloaded ZIPs are deleted at check completion.

**A1 does not create approvals or metadata PRs, collect/monitor new versions or publish stable.** Static validation is not code safety, source/binary correspondence or in-game compatibility. Reports list actual CLR references for later review; dependency closure and approved update scope follow in later batches. The official index remains empty, and the client's current `phinix.managed` staging source is unchanged.

## Maintainer actions

No new secrets are needed now. Review applications/reports and decide first-time admission once A2–A4 are connected; ordinary later versions should not require repeated manual approval. Plain comments or arbitrary labels are not approvals.

For retries use Actions → Plugin intake → Run workflow with the issue number, or:

```sh
# Trusted validator/self-check only; no application or publication.
gh workflow run plugin-intake.yml --repo HunYuan2333/Phinix-Plugin-Index -f issue_number=0
# Replace 123 with the real submission number; checks/reports, never publishes.
gh workflow run plugin-intake.yml --repo HunYuan2333/Phinix-Plugin-Index -f issue_number=123
gh run list --repo HunYuan2333/Phinix-Plugin-Index --workflow plugin-intake.yml --limit 5
# Replace RUN_ID.
gh run view RUN_ID --repo HunYuan2333/Phinix-Plugin-Index --log-failed
```

Forms/Issue events require the workflow on the default branch. Checkouts pin the trusted event commit and retain no git credentials. Never checkout/build author scripts with publication credentials. Read-only checks and issue-report writes use separate jobs. Official Actions pin full commit SHAs; candidate text is not interpolated into shell commands. Do not include secrets or private data in applications.

## A2 → A3 → A4

| Batch | Delivery | Activation/acceptance |
| --- | --- | --- |
| A1 | Current submission, fixed-candidate check and report delivery | Trusted CI, real asset checks and automatic issue report; no first-time approval |
| A2 | Bot metadata-only PR; maintainer approval of the exact candidate; persistent identity/time/issue/source/update-scope records in reviews and packages | Changed candidates invalidate approval; unauthorized reviewers cannot approve; recheck changed assets; keep permanent report digest |
| A3 | Check approved public sources roughly every six hours with manual retry; revalidate complete published releases and automatically accept normal versions inside policy | Never replace bytes of accepted versions; owner/repository/channel changes require review; recalculate dependency closure within allowed scope or pause; retain old versions on failure |
| A4 | Serialized validation of approved inputs and full dependency closure; catalog → fixed published release → verify assets → immutable published description → stable last; gateway integration | Failures/retries/concurrency never break prior stable; directly invoke trusted publishing instead of assuming bot tag pushes trigger another workflow; real client download acceptance before enabling automatic publication |

Configure minimal PR/content write permissions when A2/A4 are implemented and validated, not in A1. Design branch/review rules alongside automatic ordinary updates rather than requiring manual approval for every version. Changes to trusted validator/publisher code remain maintainer-reviewed.

A4 does not change Cloudflare sources/defaults/R2 until deployment configuration is concrete. Workflow artifacts are not permanent download links. Catalog schema is v2; future changelog fields require synchronized publisher/client format support.

A GitHub App is deferred until cross-repository triggers, a distinct bot identity or finer installation scope are needed; then restrict installation to the index and provision App ID/private key separately. Authors do not supply tokens. AI source review is a later auxiliary step; this batch uses no model key or calls.

## Local maintenance

```sh
dotnet build Validator/Validator.csproj --configuration Release
python3 -m unittest discover -s tests -v
python3 scripts/bot.py check --input examples/managed-submission.json --validator Validator/bin/Release/net10.0/Validator.dll --output /tmp/phinix-bot-new-check
```

The last command performs real GitHub requests; use a new output directory. `Validator/Production` is an explicit production source snapshot with origins/hashes in `production-provenance.json`. Refresh deliberately, validate regressions/real assets, and never fetch a mutable framework main branch during checks. Do not store author binaries, game references, credentials or private logs in the index.

References: [GITHUB_TOKEN](https://docs.github.com/en/actions/tutorials/authenticate-with-github_token), [workflow triggering](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow), [Actions permissions API](https://docs.github.com/en/rest/actions/permissions). Ordinary tag pushes by `GITHUB_TOKEN` do not trigger another workflow; PR opened/synchronize/reopened can require approval to run. Publication must use an explicit orchestration path.
