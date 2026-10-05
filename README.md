# Phinix Plugin Index

[中文](README.zh-CN.md). The official Phinix managed-plugin catalog. Authors keep source and fixed DLL ZIP releases in their own public repositories; this repository stores reviewed metadata and immutable catalog snapshots.

Submit through the Plugin submission Issue form. Maintainers approve the exact candidate by adding `plugin-approved`; trusted checks create/merge an audit PR and publish automatically. Publication closes the Issue; failures keep it open with `plugin-error` and author guidance. Close an unapproved Issue to reject it. [Author and bot guide](GitHubBotGuide.md) · [Maintainer publication guide](ControlledPublication.md).

The official source is `phinix.official`. Player clients default to GitHub direct and can switch to CF acceleration for the same catalog. `stable.json` points to the current immutable schema-v3 catalog Release; files on a development branch and test fixtures are not player publication.

The Playtest developer fixture is excluded from the player catalog. It remains independently available in [Phinix-PluginStore-PoC](https://github.com/HunYuan2333/Phinix-PluginStore-PoC). The official catalog now includes the harmless [Example Plugin](https://github.com/HunYuan2333/Phinix-Example-Plugin), demonstrating normal submission, localization, tabs and settings. Approved fixture records and historical snapshots remain for audit, not as store listings. Maintainers own `catalog-exclusions.json`; exclusions never rewrite approved artifacts/locks and publication validates the visible dependency closure.

Workflows, trusted Validator sources and regression fixtures are maintenance infrastructure. Do not upload credentials, author binaries, game/Unity DLLs or server state. Metadata approval is not certification of code safety. [Client development](https://github.com/HunYuan2333/Phinix-Rework).
