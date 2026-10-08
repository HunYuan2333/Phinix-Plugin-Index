# 宿主模块清单

[English](HostModules.md)。`host-module-profiles.json` 是维护者配置，由主包实际 DLL 的模块属性发现生成，不加载或执行插件代码。发布检查把宿主图与选中插件包图合并；校验器没有具名插件/模块例外。

清单的范围必须覆盖所有选中插件声明的 Phinix 范围。缺少配置不会授予宿主能力。未知依赖、循环、冒充宿主模块/程序集、重复或未知字段、多份适用清单歧义均拒绝。玩家安装/启动仍检查真实 Host 模块、启用状态、程序集和兼容性；不是作者自报，也不替代游戏实际可用性。

在主体仓库构建干净产物后，使用 English 页的 `--export-host-profile` 命令生成新文件，审阅适用版本和发现的依赖图，再通过正常代码 PR 更新配置。每个程序集记录 SHA-256；导出仅读取直接 DLL 并限制输入，不执行构造器或属性。本次开发清单来自 2026-10-06 主包，8 个程序集/5 个模块。主包改变后重新发现，不把业务 ID 写进校验器分支，也不删除插件真实依赖以绕过发布检查。

## F6 拆仓来源检查点（2026-10-08）

从拆分后的 Phinix-Rework 客户端产物重新导出清单：8 个程序集、相同的 5 模块依赖图。历史目录、审批记录和已发布 ZIP 不重写。

`Validator/production-provenance.json` schema 2 分别记录 Client 与 Common 的正式仓库和完整固定提交，每份冻结源码注明归属。CI 只校验冻结文件完整性时运行 `python3 scripts/validator_snapshot.py check`，不需要业务源码 checkout。

需要比对源码时，使用记录提交上的两个可信 checkout：

```sh
python3 scripts/validator_snapshot.py check --client-root /path/to/Phinix-Rework --common-root /path/to/Phinix-Rework-Common
```

显式刷新使用同样的两个根目录；升级来源时同时提供 `--client-commit 完整SHA --common-commit 完整SHA`。必须满足正式 origin、HEAD 和 Client 固定 Common gitlink 一致，选中工作文件与提交 blob 一致；脏源码、错误固定引用、越界和跨归属源码在写入前拒绝。保留 schema 1 单仓历史 fixture 支持；schema 2 不接受 `--source-root`。候选插件仓库或浮动分支不能作为刷新来源。
