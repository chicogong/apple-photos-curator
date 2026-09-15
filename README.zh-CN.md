# Apple Photos Curator

[English](README.md) | 中文

## 中文说明

这是一个面向 Codex 的 Apple Photos 安全整理 Skill：先审计、再设计、后执行，帮助整理相簿与文件夹，同时避免误改 GPS、误处理隐藏照片或误删媒体。

本仓库是通用、隐私安全的公开版本，不包含照片、Photos 数据库、缩略图、OCR 导出、精确坐标、删除清单或任何个人整理报告。

### 适用场景

这个 Skill 适合以下类型的任务：

- **相簿与文件夹设计**：按地点、时间、人物、来源、媒体类型和复核状态重新规划结构。
- **旅行与地点整理**：识别重复到访、旅行批次、城市与有纪念意义的小地点；对证据不足的地点保留待复核队列。
- **GPS 异常排查**：检查国家、城市与照片内容、时间、邻近照片是否相符；不会仅凭地图显示就猜测并改写 GPS。
- **隐藏与私密媒体**：保持隐藏状态，单独处理敏感资料；只有明确授权并完成系统认证后，才考虑“解除隐藏—建立关系—重新隐藏”的闭环。
- **截图、文档和二维码**：按用途分为资料、卡包、重要信息、有意思的内容和人工待清理，不把 OCR 缺失或分辨率低直接当作删除依据。
- **视频与 Live Photo**：区分视频、Live Photo 和特殊媒体，优先做可验证的归类，不仅凭文件名推断内容。
- **外部存储去重**：只有在字节级 SHA-256、媒体有效性、相簿关系、隐藏状态和保留副本都核对后，才提出外部副本删除候选。
- **本地同步检查**：在不访问云服务的前提下检查本机 Photos 状态、计数、隐藏数量和相关队列；云端问题单独说明边界。

### 不会自动做的事

以下操作不是默认行为，必须有单独、明确的授权和可回滚方案：

- 直接修改 `Photos.sqlite` 或 Photos Library 包内部文件；
- 根据国家、城市、文件名或单张照片自动改 GPS；
- 为了整理而解除隐藏、导出隐私缩略图或 OCR 原文；
- 仅凭文件名、大小、时长或相似外观删除照片、视频或外部硬盘文件；
- 把旧相簿关系当成错误并批量移除；
- 未确认同步稳定性前执行批量变更；
- 在用户要求本地处理时访问云服务。

### 推荐工作流程

```text
范围确认
   ↓
只读审计（数据库副本 + WAL/SHM）
   ↓
整理方案与 dry-run（不改变媒体）
   ↓
用户确认具体批次
   ↓
通过 Photos UI 或 PhotoKit 小批量执行
   ↓
重新审计：计数、隐藏状态、指纹、相簿关系、同步状态
   ↓
记录变更、排除项、删除项和下一步
```

每一轮都要把“相簿关系变化”和“媒体变化”分开报告。加入一个相簿只增加引用，不会复制原始媒体；删除媒体则必须另行确认。

### 使用方法

#### 1. 在 Codex 中使用

Skill 被明确安装到某个 Codex 环境后，可用类似下面的请求开始：

```text
使用 apple-photos-curator。
先只读审计我的 Apple Photos，给出相簿/文件夹整理方案和 dry-run。
不要改 GPS，不要解除隐藏，不要删除照片；先报告风险和待确认项。
```

适合分阶段提出请求：

```text
只检查旅行地点的重复、漏项和明显异常，保留现有相簿关系。
```

```text
对已经确认的这一批相簿引用执行整理，仍然不删除媒体；完成后复核计数和隐藏数量。
```

```text
检查外部硬盘候选重复文件。只列出字节完全一致且 Photos 已有保留副本的项目，不要先删除。
```

本仓库本身不会自动把 Skill 安装到开发机器；安装与启用应由使用者明确控制。

#### 2. 运行只读审计脚本

脚本会把 `Photos.sqlite` 以及存在的 WAL/SHM sidecar 复制到临时目录，以只读方式查询，并只输出聚合统计和元数据指纹。它不会写入 Photos Library，也不会读取或删除原始媒体。

```bash
cd /path/to/apple-photos-curator
mkdir -p reports
python3 skills/apple-photos-curator/scripts/audit_photos_library.py \
  --library "/path/to/Photos Library.photoslibrary" \
  --output reports/audit.json
```

输出包含数据库 `quick_check`、总数、活动数、隐藏数、截图数、视频数和活动媒体元数据指纹。审计 JSON 只应保存在本地，不要提交到公开仓库。

如果机器上只有一个 `*.photoslibrary`，也可以省略 `--library`；存在多个图库时必须显式指定。

#### 3. 发布前检查

```bash
python3 scripts/validate_skill.py .

python3 skills/apple-photos-curator/scripts/validate_skill.py \
  skills/apple-photos-curator

python3 /path/to/skill-creator/scripts/quick_validate.py \
  skills/apple-photos-curator

python3 skills/apple-photos-curator/scripts/scan_release_privacy.py .
python3 -m py_compile skills/apple-photos-curator/scripts/*.py
```

根级 validator 负责 Chicogong 共享仓库契约和行为用例 schema；Skill 内 validator 与隐私扫描继续由本产品维护。隐私扫描会拒绝常见的本地路径、邮箱、UUID、精确坐标、令牌和敏感文件模式。这些检查不替代人工 review，也不证明 Agent 运行时行为已经通过。

### 整理决策原则

#### 相簿与文件夹

- 用较浅的层级承载稳定维度：时间/事件、地点/旅行、人物、来源、截图/资料、收藏和复核队列。
- 来源与导入历史用于追溯，不作为唯一的浏览主结构。
- 文件夹只在拥有多个有意义的子相簿时使用；不为了凑 iOS 四宫格制造空相簿。
- 旧相簿通常先保留，新增覆盖视图并完成计数核对后，再讨论是否退役旧结构。
- 反复到访的城市或校园可以按不重叠时间段拆分；小地点只有在照片数量、内容和地理证据都稳定时才单独建相簿。

#### 隐藏、私密与低质量媒体

- 隐藏状态是保护边界，不是整理障碍；默认保持隐藏。
- 老手机、低分辨率、模糊或 OCR 缺失只是人工复核信号，不等于无价值。
- 卡包、证件、二维码、账号信息和私密人物照片应与普通回忆相簿分开。
- 任何“解除隐藏后加入相簿再隐藏”的方案，都必须先冻结精确清单，执行后逐项验证清单和隐藏数量一致。

#### 重复与外部硬盘

外部文件只有同时满足以下条件，才可以进入“可删除候选”：

1. 与已保留副本做字节级 SHA-256 比对；
2. 确认文件可正常读取、类型和时长一致；
3. 核对 Photos 中的相簿关系、隐藏状态和重要标记；
4. 确认保留副本可访问，并记录恢复路径；
5. 重新展示精确候选清单，由用户确认后再执行删除。

### 目录结构

```text
.
├── README.md                         # 英文仓库说明
├── README.zh-CN.md                   # 中文仓库说明
├── LICENSE
├── SECURITY.md                       # 私密漏洞报告策略
├── .skill-studio.json                # Studio 托管文件边界
├── .github/workflows/validate.yml    # 产品自有的组合 CI
├── scripts/validate_skill.py         # Studio 托管的仓库契约
├── tests/
│   └── apple-photos-curator.behavior.json  # 行为用例，不匹配固定答复
└── skills/apple-photos-curator/
    ├── SKILL.md                      # Skill 入口和核心工作流
    ├── agents/openai.yaml             # Codex UI 元数据
    ├── references/
    │   ├── album-design.md            # 相簿命名、拆分和文件夹层级规则
    │   └── safety-gates.md            # 授权、基线、变更和验收门槛
    └── scripts/
        ├── audit_photos_library.py   # 只读聚合审计
        ├── scan_release_privacy.py    # 发布隐私扫描
        └── validate_skill.py          # Skill 结构校验
```

Skill 包内刻意不放 README、照片、数据库副本、报告或安装脚本；这些内容属于仓库说明或使用者自己的本地环境。

Skill Studio 只管理 `.skill-studio.json` 中声明的根级 `scripts/validate_skill.py`。本仓库继续拥有 workflow 和产品专属检查；Studio 升级不得覆盖它们。

### 验收标准

一次整理只有在以下项目都符合预期时才算完成：

- 数据库 `quick_check` 正常；
- 相簿整理前后媒体总数和活动媒体指纹符合预期；
- 隐藏数量没有未经授权的变化；
- 受保护相簿关系保持不变；
- 目标相簿引用完整且 dry-run 不再产生意外增量；
- 本地同步状态稳定；
- 删除项、排除项和未决项都有明确记录。

发现任何无法解释的计数、指纹、隐藏状态或相簿关系变化，都应停止后续操作并重新审计。

### 许可证

MIT。
