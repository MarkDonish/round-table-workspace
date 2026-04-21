# Skill Compatibility Check

检查日期：2026-04-08

## 结论

当前目录下已经存在大量名人 skill 相关文件与引用方式，新建框架需要兼容这些现有结构。

兼容性结论：`已兼容，不建议改动本地 skill 目录结构`

## 已发现的现有结构

### 1. 本地已安装的精确 skill 目录

位于：`C:\Users\CLH\.codex\skills`

已确认存在：

- `steve-jobs-skill`
- `elon-musk-skill`
- `munger-skill`
- `feynman-skill`
- `naval-skill`
- `taleb-skill`
- `zhangxuefeng-skill`
- `paul-graham-skill`
- `zhang-yiming-skill`
- `karpathy-skill`
- `ilya-sutskever-skill`
- `mrbeast-skill`
- `trump-skill`

### 2. 当前目录下已存在的 skill 相关文件

- `C:\Users\CLH\skill-install-report-2026-04-08.md`
- `C:\Users\CLH\skill-trigger-guide-2026-04-08.md`
- `C:\Users\CLH\AGENTS.md`
- `C:\Users\CLH\docs\skill-map.md`
- `C:\Users\CLH\docs\router.md`
- `C:\Users\CLH\prompts\*.md`
- `C:\Users\CLH\examples\*.md`

### 3. 已存在的调用方式

当前本地已经有两种并存的调用方式：

- 精确 skill 名调用：例如 `用 steve-jobs-skill ...`
- 文档中的角色化简称：例如 `Jobs + Munger + Taleb`

## 风险点

如果框架只使用简称，而不说明与本地 skill 名的对应关系，后续会出现两个问题：

1. 阅读时明白，但真正调用时不知道该写哪个精确名字
2. 后续可能误以为需要重命名本地 skill 目录，破坏现有结构

## 已采取的兼容措施

我已经补充了两层兼容规则：

1. 在 `AGENTS.md` 中追加“Compatibility With Local Skill Invocation”章节
2. 在 `docs/router.md` 中追加“与本地 skill 调用方式的兼容规则”章节

## 兼容后的使用规则

- 阅读框架时：可以继续使用人名或简称
- 真正调用时：优先使用本地精确 skill 名
- 不重命名本地 skill 目录
- 不假设存在未安装的别名 skill

## 推荐示例

- 框架写法：`Paul Graham + Jobs + Munger`
- 实际调用：`paul-graham-skill + steve-jobs-skill + munger-skill`

- 框架写法：`Feynman + Karpathy`
- 实际调用：`feynman-skill + karpathy-skill`

- 框架写法：`MrBeast + Jobs + Zhang Yiming + Munger`
- 实际调用：`mrbeast-skill + steve-jobs-skill + zhang-yiming-skill + munger-skill`
