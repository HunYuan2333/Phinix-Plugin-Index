# 准入与受控发布

[English](ControlledPublication.md)。2026-10-05，A2 与手动触发的 A4；尚未启用 A3 定时追踪。

可信索引工作流批准一个确定的候选，把永久证据写入仅含元数据的 PR，只发布已合入的记录。检查通过、Issue 标签和评论都不等于批准。两条工作流都不会检出或执行作者代码。游戏当前测试源仍是 `phinix.managed`，正式索引输出使用 `phinix.official`。

## 需要维护者亲测的流程

1. 在 Plugin submission 表单提交现有 `examples/managed-submission.json`。等待 Plugin intake 通过，从报告复制完整的 64 位候选 SHA-256，并审阅作者源代码和静态 CLR 引用。静态校验不能证明源码与二进制对应关系或运行安全。
2. 用 admin 或 maintainer 身份，在 `main` 上运行 **Plugin admission**，填真实 Issue 编号和准确指纹。机器人重新核验 Release、Tag、源码、资产、ZIP、本地化。成功后创建 `codex/admission-RUN_ID` 和只新增三个 JSON 的 PR：候选、审核及静态证据、仅手动批准的策略；不会修改 stable。错误指纹、修改的申请、其他分支、重新运行旧批准或无权审核者都会失败。
3. 审阅 PR：检查仓库与所有者数字 ID、版本、SHA-256、模块/程序集身份、依赖 ID、语言显示和永久审核证据。用 admin 或 maintainer 身份合入，不修改这三个文件；拒绝则关闭。更正申请后须重新检查并发起新的准入运行。
4. 运行 **Plugin controlled publication**，先选 `check_only=true`。它核验成功的可信准入运行、准确合入的 PR 内容、真人合入者权限，再重新校验上游/ZIP/PE、策略、已发布版本锁和完整包/模块依赖闭包。通过后选 `check_only=false` 发布。
5. 确认日志结束于 `publication.stable_committed`，检查 `stable.json`、不可变的 `published/SNAPSHOT.json` 和固定 `catalog-v3-SNAPSHOT` Release。失败时旧入口保留；排查请提供运行编号和 stable 快照。首次人工准入后继续验收 GitHub 与 CF 的实际客户端下载，完成前不启用自动发布。

```sh
# ISSUE 和 FINGERPRINT 替换为你已审阅报告中的值。
gh workflow run plugin-admission.yml --repo HunYuan2333/Phinix-Plugin-Index --ref main -f issue_number=ISSUE -f candidate_sha256=FINGERPRINT
gh run list --repo HunYuan2333/Phinix-Plugin-Index --workflow plugin-admission.yml --limit 5
# 审阅并合入生成的准入 PR 后：
gh workflow run plugin-publish.yml --repo HunYuan2333/Phinix-Plugin-Index --ref main -f check_only=true
# 上一步通过后再执行：
gh workflow run plugin-publish.yml --repo HunYuan2333/Phinix-Plugin-Index --ref main -f check_only=false
```

不需要新 token。仓库默认工作流权限仍为只读。启用 GitHub 合并提供的“允许 GitHub Actions 创建和批准 PR”设置以允许机器人创建 PR；我们的流程不提交批准评论，发布必须验证真人合入者。仅提案任务申请 contents/PR 写权限，仅发布任务申请 contents 写权限，检查任务为只读。CF 只读 token 独立使用。[GitHub 设置说明](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository)。

## 永久记录与策略

路径使用包 ID 的 SHA-256 和候选 SHA-256，每个批准版本在 `packages`、`reviews`、`policies` 各存一个文件。证据记录源 ID、规范化候选哈希、Issue 编号/正文哈希/修改时间、批准 UTC 时间、审核者登录名/数字 ID、可信工作流/运行/提交/尝试次数、完整静态报告及哈希、策略哈希。策略固定公开仓库/所有者数字身份、渠道、管理方式、程序集/模块名和依赖 ID。

本批策略是 **manual-only**。后续 A3 需要另行审核普通更新范围和追踪器；现在保存身份不等于启用自动更新。禁止重新运行旧准入以避免审核者变化，重试需启动新运行。已发布版本写入不可变 `publication-locks`，绑定版本、候选与资产哈希，不允许删除记录或改变内容；撤回版本需要后续明确策略。历史 Issue 修改不会使已锁定版本失效，但新版本发布前必须保持申请正文不变。

## 发布与故障恢复

两条工作流共用 `index-metadata` 串行队列，不取消正在运行的任务。发布器取当前可信 main 提交作为输入/快照，生成并校验完整 v3 目录，创建固定草稿 Release，无覆盖上传，下载核验字节/大小/哈希及 Tag/源码身份，再公开 Release。最后用一个 Git 提交加入不可变 published、版本锁及 stable。新鲜主分支检查与禁止强制的快进更新避免竞争覆盖。人工并发提交会阻止旧输入发布，需要在新 main 上启动新运行。[Git 引用 API](https://docs.github.com/en/rest/git/refs)。

重试复用已上传且完全匹配的资产，绝不覆盖。若 stable 已提交而成功响应丢失，重新运行会核验准确的直接子提交与已下载目录，输出 `publication.already_complete` 而不写入。指针提交失败留下的 Release 是未引用的固定快照，玩家入口仍有效。不能删除或重定向已发布 Release/Tag/资产。受控发布显式调用，不依赖 token 推送触发另一条工作流。[GITHUB_TOKEN 触发规则](https://docs.github.com/en/actions/concepts/security/github_token)。

初始限制：八个批准的版本记录、总 ZIP 下载 512 MiB、512 次 API 调用、25 分钟操作期限，加上已有每包和 JSON 限制。超限关闭发布，大目录需要专门扩容。闭包检查包版本范围、存在时的可选依赖、包/模块环以及程序集/模块冲突。本批尚无宿主模块白名单，因此拒绝依赖未出现在包闭包中的宿主模块 ID。客户端仍核验宿主/游戏版本、本地安装状态和实际 CLR 引用可用性。

## 开发验证

在 Phinix 工作区运行：

```sh
dotnet build Extensions/PluginStore/RepositoryAutomation/Validator/Validator.csproj --configuration Release --no-restore -p:BuildInParallel=false -m:1
python3 -m unittest discover -s Extensions/PluginStore/RepositoryAutomation/tests -v
```

索引仓库对应路径是 `Validator/Validator.csproj`、`tests`。测试覆盖批准证据和准确合入的 PR、指纹/权限/分支/申请变动、策略/报告篡改、版本连续性、部分上传重试/资产替换、发布失败/并发修改保持指针、原子 stable 最后提交和真实校验器的依赖/模块闭包。真实公开回源与完整 Actions 流程仍需要远端验收；控制台测试不代表游戏内验证。
