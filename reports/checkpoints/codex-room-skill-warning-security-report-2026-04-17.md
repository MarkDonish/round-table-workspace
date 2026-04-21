# Codex 本地黄色警报安全汇报

生成时间：2026-04-17
检查对象：`C:\Users\CLH\.codex\skills\room-skill\SKILL.md`
告警原文：`missing YAML frontmatter delimited by ---`

## 1. 结论摘要

本次黄色警报的根因是 `room-skill` 的 `SKILL.md` 文件头包含 UTF-8 BOM 字节序标记（`EF BB BF`），导致 Codex 的技能加载器未将文件首部识别为严格的 `---` YAML frontmatter 起始符。

本次告警属于：

- 本地文件编码兼容问题
- 技能加载失败/降级问题
- 非高危安全事件

当前未发现：

- 恶意注入内容
- 非授权文件落地
- 多个技能被批量污染
- 明显的持久化攻击痕迹

## 2. 现场证据

### 2.1 文件存在且内容结构正常

`C:\Users\CLH\.codex\skills\room-skill\SKILL.md` 的正文开头可见标准 frontmatter 结构：

```md
---
name: room-skill
description: |
  ...
---
```

说明问题不在于“缺少 frontmatter 文本”，而在于“加载器没有把文件头当作纯 `---` 识别”。

### 2.2 原始字节命中 UTF-8 BOM

对目标文件执行十六进制检查，文件前 4 个字节为：

```text
EF BB BF 2D
```

对应含义：

- `EF BB BF` = UTF-8 BOM
- `2D 2D 2D` = `---`

即文件真实起始并不是 `---`，而是 `BOM + ---`。

### 2.3 正常技能文件对照

对照文件：

`C:\Users\CLH\.codex\skills\debate-roundtable-skill\SKILL.md`

其开头字节为：

```text
2D 2D 2D 0A
```

即直接以 `---` 开头，无 BOM。

### 2.4 范围扫描结果

已扫描 `C:\Users\CLH\.codex\skills\` 下所有 `SKILL.md`。

结果：

- 发现带 UTF-8 BOM 的 `SKILL.md` 只有 1 个
- 唯一命中路径为：`C:\Users\CLH\.codex\skills\room-skill\SKILL.md`

说明当前问题是单点文件问题，不是全局批量异常。

### 2.5 文件元数据

- 路径：`C:\Users\CLH\.codex\skills\room-skill\SKILL.md`
- 大小：`22880` 字节
- 最后写入时间：`2026-04-16 23:40:50`
- SHA256：`1A09ECD4607582F0D8F0C96156C3778747EC9DCF663462A8CE93DAEDD3478F39`

## 3. 风险判断

### 风险等级

低风险

### 判断依据

1. 告警内容是解析失败，不是执行失败后的异常行为。
2. 文件主体内容可读，未见插入型 payload、可疑下载命令、可执行脚本片段或外链投毒。
3. 异常具有强一致性：仅 1 个文件、且正好命中编码级 BOM 特征。
4. 其余技能文件未出现同类批量污染迹象。

## 4. 影响评估

已确认影响：

- `room-skill` 会被 Codex 启动时跳过加载
- 与 `/room` 相关的 skill 路由能力可能失效或不可用
- 启动时出现黄色警报，影响可观测性

未确认但可能存在的次级影响：

- 同一启动过程里该 skill 可能被扫描两次，因此告警重复显示两次

关于上条，仅凭当前材料无法确认具体扫描机制，结论应标记为推断，不作为已证实事实。

## 5. 安全结论

本次黄色警报更接近“配置/编码兼容故障”，不是“安全入侵事件”。

可将其定性为：

- 安全性：当前未见恶意迹象
- 完整性：文件内容大体完整
- 可用性：`room-skill` 加载失败，存在功能降级

## 6. 建议处置

建议按低风险故障处理，不按安全事件升级。

建议操作：

1. 去除 `C:\Users\CLH\.codex\skills\room-skill\SKILL.md` 的 UTF-8 BOM，保存为 UTF-8 无 BOM。
2. 重启 Codex，确认黄色警报消失。
3. 如仍重复告警，再继续检查 skill loader 的扫描去重逻辑。
4. 在变更前保留当前 SHA256 或备份一份原文件，便于回滚。

## 7. 当前未做事项

- 未修改原文件
- 未重启 Codex 复测
- 未追踪 Codex loader 源码，因此“为何重复报两次”目前为 `信息缺失`

## 8. 最终判定

最终判定：低风险、本地编码兼容问题、非入侵、建议修复。
