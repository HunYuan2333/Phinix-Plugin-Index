# GitHub 插件索引机器人操作说明

2026-10-05：正常准入改为维护者给 Issue 加一次 `plugin-approved` 标签，证据 PR 合入和发布自动完成。见[当前操作说明](ControlledPublication.zh-CN.md)。下方旧 A2/A4 待实施说明为历史记录；A3 尚未启用。


[English](GitHubBotGuide.md)。2026-10-05。目标仓库：[HunYuan2333/Phinix-Plugin-Index](https://github.com/HunYuan2333/Phinix-Plugin-Index)。

首版采用 GitHub Actions，报告身份是 `github-actions[bot]`。不需要常驻服务器、注册 GitHub App 或提供新的个人 token。工作流使用仓库自动提供的 `GITHUB_TOKEN`，默认只读；报告任务单独申请 `issues: write`。Cloudflare 的 `GITHUB_TOKEN` 是另一份回源只读凭据，不拿来给机器人写仓库。

## 当前 A1：申请与静态报告

作者在 Issues → New issue → Plugin submission 提交固定候选。复制 [示例](examples/managed-submission.json)，将全部字段换成自己的包，包括公开仓库、作者/仓库 ID、源码提交、正式 Release/资产 ID、manifest、大小和摘要。示例是真实 Playtest 1.3.0 的测试输入，也已作为获准的正式条目。申请标题以 `[Plugin]` 开头，表单生成 `Candidate JSON` 段。

机器人在申请新建、编辑或重新打开时检查：

1. 用与客户端相同的严格 schema-v3 目录读取器验证候选声明。
2. 核对公开仓库/作者数字身份、正式非预发布 Release、固定 tag 对应的源码 commit、公开 C# 源码树、资产身份/归属/大小。
3. 只从 GitHub API 和指定资产 CDN 下载，计算真实 SHA-256；用生产 ZIP/PE/CLR 元数据校验器检查清单、文件路径/集合/长度/摘要、目标框架、程序集及模块入口声明。作者 DLL 不被加载或执行。
4. 输出 `candidate.json`、`static.json`、`report.json`，绑定规范化候选摘要及申请正文摘要/更新时间。检查及回报前再次核对申请；变化则停止旧报告。
5. `github-actions[bot]` 在未变化的申请下回报通过/失败及候选指纹。报告工件保留 14 天，下载 ZIP 随检查结束删除。

**A1 不创建批准记录，不生成条目 PR，不自动收录/监控新版本或发布 stable。** 静态通过不是代码安全、源码与 DLL 对应关系或实际游戏兼容的证明；报告列出实际 CLR 引用供后续审查。依赖闭包、批准范围和正式升级由后续批次接续。当前正式索引已有获准的 Playtest 1.3.0，不改变客户端使用的 `phinix.managed` staging 来源。

## 你现在需要做什么

没有新的密钥配置。维护工作是查看作者申请和检查报告，决定首次收录；不会要求每个正常后续版本重复人工审批。首次批准与索引发布要在 A2–A4 接通后才正式生效，不使用普通评论或任意标签冒充批准。

需要手动重试时，网页选择 Actions → Plugin intake → Run workflow，填申请编号；或在终端运行：

```sh
# 只检查可信工具和回归，不申请或上架插件。
gh workflow run plugin-intake.yml --repo HunYuan2333/Phinix-Plugin-Index -f issue_number=0

# 将 123 换成实际插件申请编号；这会检查并回报，不会发布。
gh workflow run plugin-intake.yml --repo HunYuan2333/Phinix-Plugin-Index -f issue_number=123
gh run list --repo HunYuan2333/Phinix-Plugin-Index --workflow plugin-intake.yml --limit 5
# 将 RUN_ID 换成运行编号。
gh run view RUN_ID --repo HunYuan2333/Phinix-Plugin-Index --log-failed
```

自动表单和 Issue 事件须工作流进入默认分支后才生效。工作流在索引仓库内运行，checkout 固定本次可信提交且不保留 git 凭据，不 checkout 作者仓库执行 MSBuild/脚本。报告任务与只读检查任务分开。官方 Actions 固定完整提交 SHA；候选字段不拼进 shell 命令。作者申请里不要填写凭据或私人数据。

## 接下来按 A2 → A3 → A4 接通

| 批次 | 交付 | 验收及开启条件 |
| --- | --- | --- |
| A1 申请/检查/报告 | 本轮交付；固定候选与生产静态校验 | 可信工具 CI、真实资产检查、Issue 自动报告；不授予首次批准 |
| A2 首次批准与条目 PR | 机器人生成只含元数据的 PR；维护者审查具体指纹，记录身份、时间、申请、来源与后续允许范围 | 修改申请/候选使旧批准失效；无维护权限的人不能批准；批准前后资产变化仍拒绝；报告永久摘要进入 `reviews/`，条目进入 `packages/` |
| A3 正常版本自动检查 | 约每六小时检查已批准公开来源，提供手动重试；正式 Release 完整后重验，符合批准规则自动形成新版目录输入 | 同版本不得换字节；仓库/作者/渠道身份变化暂停并重审；依赖变化在批准范围内重算闭包，超出范围暂停；失败保留现有版本，不阻塞其他来源 |
| A4 固定目录发布 | 串行编排再次验证批准输入/依赖闭包，生成完整 catalog → 上传正式固定 Release → 核对资产 → 保存不可变 published → 最后更新 stable；接入正式或隔离测试 gateway 来源 | 发布中断、重试、并发和输入变化不破坏上一份 stable；工作流直接调用可信发布流程，不依赖 bot 推 tag 再触发另一个工作流；真实客户端下载验收后开启自动发布 |

A2 的机器人 PR 创建和 A4 发布需要新增最小写权限；到该批次用 CLI 配置并验证，A1 不提前赋予内容写权限。分支/审核规则与正常版本自动处理要一起设计，不能让强制人工批准所有更新与“正常版本自动更新”互相冲突。可信校验/发布脚本变动仍需维护者审查。

A4 在配置明确前不修改 Cloudflare 的来源、正式默认源或 R2 绑定。不把工作流 artifact 当作永久下载地址。当前目录为 schema v3；changelog 增加字段时必须同步发布工具和客户端严格格式支持。

GitHub App 放到跨仓库触发、独立机器人名称或更细安装授权有实际需求时再考虑。若需要，可另行配置 App ID/私钥和仅安装索引仓库；不复用 Cloudflare 回源 token，不需要作者交出 token。AI 源码审查是之后的辅助阶段，本轮不调用模型、不增加模型密钥或费用。

## 本地维护与更新可信校验器

```sh
dotnet build Validator/Validator.csproj --configuration Release
python3 -m unittest discover -s tests -v
python3 scripts/bot.py check --input examples/managed-submission.json --validator Validator/bin/Release/net10.0/Validator.dll --output /tmp/phinix-bot-new-check
```

最后一个命令有真实 GitHub 请求；输出目录必须不存在。`Validator/Production` 是明确导出的生产源码快照，来源和每文件摘要在 `Validator/production-provenance.json`。后续更新需同步真实生产改动、重跑回归和真实资产检查，不能在 Actions 中随意下载可变主分支代码。索引不保存作者二进制、游戏引用、凭据或私有日志。

参考：[GITHUB_TOKEN](https://docs.github.com/en/actions/tutorials/authenticate-with-github_token)、[工作流触发规则](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow)、[Actions 权限 API](https://docs.github.com/en/rest/actions/permissions)。`GITHUB_TOKEN` 触发的普通 tag push 不会再次运行 workflow；PR opened/synchronize/reopened 可能进入待批准运行状态，不能靠隐含触发完成无人值守发布。
