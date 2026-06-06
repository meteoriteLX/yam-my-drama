# 剧本 YAML Schema 定义

本文档定义 **yam-my-drama** 项目输出的剧本数据结构。所有 AI 转换结果、人工编辑与导出均遵循本 Schema。

- **Schema 版本**：`1.0.0`
- **文件格式**：YAML（UTF-8）
- **JSON Schema 校验文件**：[../schemas/script.schema.json](../schemas/script.schema.json)

---

## 1. 设计目标

小说与剧本是两种截然不同的叙事媒介：

| 维度 | 小说 | 剧本 |
|------|------|------|
| 叙事方式 | 作者全知视角、心理描写、旁白 | 可视化动作 + 对白，由导演/演员呈现 |
| 结构单位 | 章节、段落 | 幕（Act）→ 场（Scene） |
| 时间空间 | 可跳跃、可模糊 | 每场需明确 INT/EXT、地点、时间 |
| 读者/观众 | 阅读文字 | 观看画面与表演 |

本 Schema 的设计目标是：**让 AI 生成的初稿既符合影视剧本行业习惯，又保留与原著小说的溯源关系，便于作者二次打磨。**

---

## 2. 顶层结构

```yaml
schema_version: "1.0.0"
meta: { ... }
characters: [ ... ]
acts: [ ... ]
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `schema_version` | string | 是 | Schema 版本号，用于向后兼容 |
| `meta` | object | 是 | 剧本元信息 |
| `characters` | array | 是 | 人物表（至少 1 人） |
| `acts` | array | 是 | 幕列表（至少 1 幕，每幕至少 1 场） |

---

## 3. 字段详解

### 3.1 `meta` — 元信息

```yaml
meta:
  title: "雨夜重逢"
  subtitle: ""                    # 可选，副标题
  author: "张三"                   # 剧本作者（改编者）
  source_novel:                  # 原著信息
    title: "城市边缘"
    author: "李四"
    chapters_covered: [1, 2, 3]   # 本次改编涵盖的章节号
  genre: "都市情感"                # 可选，类型标签
  logline: "一对旧日恋人在雨夜偶然重逢，往事与选择再次浮现。"  # 可选，一句话梗概
  created_at: "2026-06-06"        # 生成日期（ISO 8601 日期）
  language: "zh-CN"               # 剧本语言
  notes: ""                       # 可选，改编说明或 AI 提示
```

**设计原因：**

- `source_novel.chapters_covered` 对应题目要求的「3 个章节以上」输入范围，便于追溯改编来源。
- `logline` 帮助作者快速把握改编后的故事主线，也是向投资人/合作方 pitch 的常用格式。
- `language` 预留多语言扩展（如中英双语剧本）。

---

### 3.2 `characters` — 人物表

```yaml
characters:
  - id: "char_linwan"             # 全局唯一 ID，供 dialogues 引用
    name: "林晚"
    aliases: ["晚晚"]              # 可选，昵称/别称
    description: "28 岁，独立书店店员，性格内敛。"
    role: "protagonist"            # protagonist | antagonist | supporting | extra
    first_appeared:                # 首次出场
      act: 1
      scene: "1-1"
    traits: ["内敛", "敏感"]       # 可选，性格标签，辅助 AI 保持一致性
```

**设计原因：**

- **`id` 与 `name` 分离**：多章转换时，AI 可能遇到「他」「她」等代词；统一 ID 引用可避免对白张冠李戴。
- **独立人物表**：多章 Pipeline 每章转换后需 merge 角色，人物表是跨章一致性的锚点。
- **`first_appeared`**：帮助作者检查改编节奏，确认角色引入是否过早/过晚。
- **`role`**：区分主角/配角/龙套，后续可按角色筛选场次或统计台词量。

---

### 3.3 `acts` — 幕

```yaml
acts:
  - act: 1
    title: "重逢"
    summary: "林晚与陈野在书店雨夜重逢，回忆被唤醒。"  # 可选，本幕摘要
    scenes: [ ... ]
```

**设计原因：**

- 采用 **Act → Scene** 两级结构，符合话剧/影视剧本常见组织方式。
- `summary` 便于作者纵览改编结果，也作为多章转换时「上一幕摘要」注入 AI 上下文。

---

### 3.4 `scenes` — 场

每场戏是剧本的最小可独立编辑单元。

```yaml
scenes:
  - scene_id: "1-1"               # 格式：{act}-{序号}，全局唯一
    scene_number: 1               # 本幕内场次序号
    heading:                      # 场景标题（Slug Line）
      int_ext: "INT"              # INT（内景）| EXT（外景）| INT/EXT
      location: "旧时光书店"
      time: "NIGHT"               # DAY | NIGHT | DAWN | DUSK | CONTINUOUS
      season: ""                  # 可选，SPRING | SUMMER | AUTUMN | WINTER
    source_mapping:               # 与原著的映射（改编溯源）
      chapter: 1
      paragraph_range: [1, 4]     # 对应小说段落区间（闭区间）
      excerpt: "雨下得很大，林晚合上书，听见门铃响。"  # 可选，原文摘要
    action_blocks:                # 动作/场景描述（现在时、可拍摄）
      - "雨水顺着玻璃滑落。林晚抬头，看见门口站着陈野。"
    dialogues:                    # 对白列表
      - character_id: "char_chenye"
        line: "好久不见。"
        parenthetical: "低声"       # 可选，语气/伴随动作
        emotion: "克制"            # 可选，情绪提示
    transition: "CUT TO:"         # 可选，转场方式（FADE IN / CUT TO / DISSOLVE TO 等）
    duration_estimate: "2min"     # 可选，预估时长
    notes: ""                     # 可选，改编备注（如「小说心理描写改为动作」）
```

**设计原因：**

- **`heading`**：INT/EXT + 地点 + 时间是行业标准 Slug Line，可直接映射为 Fountain 等格式。
- **`source_mapping`**：这是本项目的核心创新点之一——作者可对照原著检查 AI 改编是否 FAITHFUL，也方便「重新生成单场」时定位原文。
- **`action_blocks` 为数组**：一段动作一行，便于 diff、拖拽排序和逐条 AI 重写。
- **`dialogues` 与 `action_blocks` 分离**：小说是「叙述 + 对话」混合体；剧本必须拆分「可拍的」与「可说的」。
- **`parenthetical` / `emotion`**：对应剧本中的括号提示，指导表演但不计入正式台词。
- **`transition`**：保留转场语法，方便后续导出为标准剧本格式。

---

### 3.4.1 `dialogues` 条目

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `character_id` | string | 是 | 引用 `characters[].id` |
| `line` | string | 是 | 台词正文 |
| `parenthetical` | string | 否 | 括号内表演提示，如「冷笑」「顿了顿」 |
| `emotion` | string | 否 | 情绪标签，便于后续 AI 润色 |
| `voice_over` | boolean | 否 | 是否为画外音/旁白（默认 `false`） |

**关于旁白/心理描写的处理：**

小说中大量心理活动不应直接变成角色对白。Schema 通过两种方式处理：

1. 转化为 `action_blocks`（外化动作）
2. 必要时使用 `voice_over: true` 标记画外音，并在 `notes` 中注明改编策略

---

## 4. 完整示例（精简）

完整示例见 [../examples/sample_script.yaml](../examples/sample_script.yaml)。

```yaml
schema_version: "1.0.0"

meta:
  title: "雨夜重逢"
  author: "张三"
  source_novel:
    title: "城市边缘"
    author: "李四"
    chapters_covered: [1, 2, 3]
  created_at: "2026-06-06"
  language: "zh-CN"

characters:
  - id: "char_linwan"
    name: "林晚"
    role: "protagonist"
    first_appeared: { act: 1, scene: "1-1" }

acts:
  - act: 1
    title: "重逢"
    scenes:
      - scene_id: "1-1"
        scene_number: 1
        heading:
          int_ext: "INT"
          location: "旧时光书店"
          time: "NIGHT"
        source_mapping:
          chapter: 1
          paragraph_range: [1, 3]
        action_blocks:
          - "林晚合上书，门铃响起。"
        dialogues:
          - character_id: "char_linwan"
            line: "欢迎光临。"
        transition: "CUT TO:"
```

---

## 5. 设计原则总结

| 原则 | 体现 |
|------|------|
| **可编辑** | 层级清晰，字段语义明确，可用文本编辑器或 YAML 编辑器直接修改 |
| **可溯源** | `source_mapping` 关联原文章节与段落 |
| **可扩展** | 可选字段丰富，不破坏必填核心；`schema_version` 支持版本演进 |
| **可校验** | 提供 JSON Schema，后端/前端可自动验证结构 |
| **可转换** | 字段命名对齐 Fountain/Final Draft 概念，便于后续格式导出 |
| **AI 友好** | 结构化输出降低 LLM 幻觉；人物 ID 引用减少角色混淆 |

---

## 6. 版本演进策略

- **Patch（1.0.x）**：新增可选字段，不影响旧文件解析。
- **Minor（1.x.0）**：新增必填字段时，需提供迁移脚本或默认值。
- **Major（x.0.0）**：顶层结构变更，需更新转换 Pipeline 与文档。

当前版本 **1.0.0** 为初始发布，后续 PR 中的 AI Pipeline 与 YAML 校验器均以此为准。

---

## 7. 相关文件

| 文件 | 说明 |
|------|------|
| [examples/sample_script.yaml](../examples/sample_script.yaml) | 符合本 Schema 的完整示例剧本 |
| [examples/sample_novel.txt](../examples/sample_novel.txt) | 对应的 3 章样例小说原文 |
| [schemas/script.schema.json](../schemas/script.schema.json) | JSON Schema 校验定义 |
