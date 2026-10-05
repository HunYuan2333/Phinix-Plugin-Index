# Admission and controlled publication

[中文](ControlledPublication.zh-CN.md). 2026-10-05. A2 and manually invoked A4; no scheduled A3 updates.

The trusted index workflow approves one exact candidate, stores permanent evidence in a metadata PR, and publishes only merged records. An intake pass, issue label or comment is never an approval. Neither workflow checks out or executes author code. The current game test source remains `phinix.managed`; official output uses `phinix.official` in the index repository.

## Maintainer acceptance

1. Submit the existing `examples/managed-submission.json` through the Plugin submission issue form. Wait for Plugin intake to pass, then copy the complete 64-character candidate SHA-256 from its report. Inspect the actual author source and static CLR references; static validation does not establish source/binary correspondence or runtime safety.
2. As an admin or maintainer, run **Plugin admission** on `main`, with the real issue number and exact fingerprint. It freshly checks the release/tag/source/asset/ZIP/localization. A successful run creates `codex/admission-RUN_ID` and a metadata PR with exactly three new JSON files: candidate, review/static evidence, and manual-only policy. It never changes stable. A wrong fingerprint, edited submission, different branch, approval rerun or unauthorized actor fails before writing the PR.
3. Review that PR. Check owner/repository numeric IDs, version, SHA-256, module/assembly identities, dependency IDs, language display and the permanent reviewer/run/source evidence. Merge it as an admin or maintainer without modifying its three files. To reject, close it. A corrected submission requires a fresh intake and approval run.
4. Run **Plugin controlled publication**, first with `check_only=true`. It verifies successful trusted admission run, exact merged PR contents and human merger identity, fresh origin/ZIP/PE checks, policy, accepted-version locks and full package/module dependency closure. After it passes, run it with `check_only=false` to publish.
5. Confirm the run ends with `publication.stable_committed`; inspect `stable.json`, the immutable `published/SNAPSHOT.json` and the fixed `catalog-v3-SNAPSHOT` Release. The old pointer remains on failure. Keep the run ID and stable snapshot when reporting failures. CLI download acceptance through GitHub and CF comes after this first human approval; automatic publication remains disabled until that acceptance passes.

```sh
# Replace ISSUE and FINGERPRINT with the report you reviewed.
gh workflow run plugin-admission.yml --repo HunYuan2333/Phinix-Plugin-Index --ref main -f issue_number=ISSUE -f candidate_sha256=FINGERPRINT
gh run list --repo HunYuan2333/Phinix-Plugin-Index --workflow plugin-admission.yml --limit 5
# After reviewing and merging the generated admission PR:
gh workflow run plugin-publish.yml --repo HunYuan2333/Phinix-Plugin-Index --ref main -f check_only=true
# Only after that check passes:
gh workflow run plugin-publish.yml --repo HunYuan2333/Phinix-Plugin-Index --ref main -f check_only=false
```

There is no new token to create. Repository default workflow permissions stay read-only. Enable GitHub's combined “Allow GitHub Actions to create and approve pull requests” setting so the bot can create PRs; these workflows never post approving reviews, and publication requires a human merger. Only PR proposal requests contents/PR write; only the publication job requests contents write. Validation has read permissions. Cloudflare's read-only token is separate. [GitHub settings](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository).

## Stored records and policy

Paths use SHA-256 of the package ID, followed by candidate SHA-256. `packages`, `reviews` and `policies` each store one file per approved version. Evidence contains source ID, canonical candidate hash, issue number/body hash/update time, approval UTC time, reviewer login/numeric ID, trusted workflow/run/commit/attempt, complete static report/hash and policy hash. Policy fixes public repository/owner numeric identities, channel, management, assembly/module names and dependency IDs.

Policy mode is **manual-only** for this controlled pilot. Later A3 needs a separately reviewed ordinary-update policy and monitor; recording identities here does not enable it. Admission reruns are rejected to avoid changing who approved an old run; start a fresh workflow instead. Previously published versions have immutable `publication-locks` binding version, candidate and artifact hashes. Their records cannot disappear or change; a retired version/withdrawal policy is a later explicit change. Historical issue edits do not invalidate already locked versions, but uncommitted new versions require the unchanged body before publication.

## Publication and recovery

Both workflows share `index-metadata` concurrency with cancellation disabled. Publisher uses current trusted main commit as input/snapshot, builds and validates the complete v3 catalog, creates a draft fixed release, uploads without clobbering, verifies downloaded bytes/size/hash and tag/source identity, then makes the Release public. Finally, one Git commit adds immutable published metadata, new version locks and stable. A fresh-head check and non-forced fast-forward update prevent competing publishers from overwriting each other. A concurrent human commit stops publication; start a new run on current main. [Git references API](https://docs.github.com/en/rest/git/refs).

Retries reuse an already uploaded matching asset and never replace it. If stable already committed and the success response was lost, retry verifies the exact direct-child pointer commit and downloaded catalog, then reports `publication.already_complete` without writes. An uploaded Release left by a failed pointer update is an unused immutable snapshot, not a broken player entry. Do not delete or retarget published releases/tags/assets. No reliance on token-generated pushes triggering another workflow; controlled publication is explicitly invoked. [GITHUB_TOKEN triggering](https://docs.github.com/en/actions/concepts/security/github_token).

The initial bounds are eight approved version records, aggregate ZIP downloads 512 MiB, 512 API calls, 25-minute operation deadline and existing per-package/JSON limits. These fail closed and need deliberate scaling before a large catalog. Closure checks select compatible package version ranges, optional dependencies when present, package/module cycles and assembly/module collisions. This pilot rejects dependencies on host-provided module IDs until an explicit reviewed host-module allowlist exists. Client host/game/installed-state and actual CLR reference availability remain game/runtime gates.

## Developer verification

From the Phinix workspace:

```sh
dotnet build Extensions/PluginStore/RepositoryAutomation/Validator/Validator.csproj --configuration Release --no-restore -p:BuildInParallel=false -m:1
python3 -m unittest discover -s Extensions/PluginStore/RepositoryAutomation/tests -v
```

In the index repository, the equivalent paths are `Validator/Validator.csproj` and `tests`. Tests cover approval proof and exact merged PR, fingerprint/role/branch/issue changes, policy/report tampering, version continuity, release partial-upload retry/replacement rejection, publication failure and concurrent-head preservation, atomic stable-last commit, and actual trusted dependency/module closure. Public origin checks and complete Actions execution still need remote acceptance; console tests do not prove in-game behavior.
