# Phinix 插件索引

目录同时支持托管 DLL 包和**仅提供元数据、链接的 Steam 工坊条目**。工坊条目使用[独立申请表单](.github/ISSUE_TEMPLATE/workshop-submit.yml)和[示例](examples/workshop-submission.json)，维护者仍加 `plugin-approved` 批准；Mod 本身由 Steam 管理。

[English](README.md)。这里是正式托管插件目录；作者在自己的公开仓库发布源码和固定 DLL ZIP，这里保存审核元数据及不可变目录快照。

作者通过 Plugin submission Issue 表单申请。维护者给准确候选添加 `plugin-approved`，机器人复核、创建并合入审计 PR、发布目录；成功自动关闭 Issue，失败保留打开状态并添加 `plugin-error` 和纠错提示。未批准时直接关闭 Issue 即为拒绝。[发布者指南](GitHubBotGuide.zh-CN.md) · [维护者发布操作](ControlledPublication.zh-CN.md)。

CF 网关正式入口为 `https://plugins.hunyuan2333.com`；[当前正式元数据](https://plugins.hunyuan2333.com/v1/sources/phinix.official/stable)。

正式源为 `phinix.official`；客户端默认 GitHub，可切换 CF 加速，访问的是同一目录。`stable.json` 指向当前 schema-v3 不可变目录 Release。开发分支文件和测试夹具不代表上架。

Playtest 测试插件从玩家目录排除，仅在独立的 [Phinix-PluginStore-PoC](https://github.com/HunYuan2333/Phinix-PluginStore-PoC) 保留。正式目录现已包含 [Phinix 示例插件](https://github.com/HunYuan2333/Phinix-Example-Plugin)，展示正规申请、多语言、Tab 和设置，不操作殖民地或物品。原测试审批和历史快照保留供追溯，不作为商店条目。维护者管理 `catalog-exclusions.json`；下架不改写已批准资产/发布锁，并重新验证可见目录依赖闭包。

Workflows、可信 Validator 和回归夹具属于维护基础设施。禁止上传凭据、作者二进制、游戏/Unity DLL 或服务器状态。审核元数据并不代表代码安全认证。[客户端开发](https://github.com/HunYuan2333/Phinix-Rework)。
