## AI小说转剧本工具
将小说文本自动转换为结构化YAML剧本初稿，辅助快速完成改编。

## Demo视频

待补充

## 项目结构

```
yam-my-drama/
├── frontend/          # Web 前端（React + Vite）
├── backend/           # API 服务（FastAPI）
├── docs/              # 文档（含 YAML Schema 定义）
├── examples/          # 示例小说与剧本
├── schemas/           # JSON Schema 校验定义
├── docker-compose.yml # 一键启动
└── README.md
```

## 技术栈

| 模块 | 技术 | 说明 |
|------|------|------|
| 前端 | React 18 + Vite 5 | 用户界面与 YAML 编辑 |
| 后端 | Python 3.11 + FastAPI | REST API 与 AI 转换 Pipeline |
| 容器 | Docker Compose | 本地一键部署 |

### 第三方依赖

| 依赖 | 用途 | 原创部分 |
|------|------|----------|
| React / Vite | 前端框架与构建 | 业务 UI 与交互逻辑 |
| FastAPI / Uvicorn | 后端 Web 框架 | 章节解析、AI Pipeline、YAML 生成 |
| httpx | HTTP 客户端 | LLM OpenAI 兼容 API 调用（原创封装） |
| （后续 PR 补充） | AI Prompt 与转换 | Prompt 工程与 Pipeline 编排 |

## 快速开始

### 方式一：Docker Compose（推荐）

```bash
docker compose up --build
```

- 前端：<http://localhost:5173>
- 后端：<http://localhost:8000>
- API 文档：<http://localhost:8000/docs>

### 方式二：本地开发

**后端**

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env   # 配置 LLM_API_KEY 等
uvicorn app.main:app --reload --port 8000
```

**LLM 配置（DeepSeek）**

在 `backend/.env` 中设置：

```env
LLM_API_KEY=your-deepseek-api-key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
LLM_TIMEOUT=120
LLM_MAX_RETRIES=2
```

> DeepSeek 使用 OpenAI 兼容接口，无需额外 SDK。API Key 请从 [DeepSeek 开放平台](https://platform.deepseek.com/) 获取，**切勿提交到 Git**（`.env` 已在 `.gitignore` 中）。

**前端**

```bash
cd frontend
npm install
npm run dev
```

浏览器访问 <http://localhost:5173>，使用小说输入界面粘贴文本或上传 `.txt` 文件，点击「解析章节」预览识别结果。

### 前端功能（PR-04）

1. **文本输入**：大文本框粘贴小说全文
2. **文件上传**：支持上传 `.txt` 文件
3. **加载样例**：一键加载内置 3 章样例小说
4. **章节预览**：展示章节列表、字数/段落统计、正文摘要（可展开）
5. **校验提示**：章节不足 3 章时显示警告，满足要求时显示通过

## API

### 章节解析

`POST /api/chapters/parse`

请求体：

```json
{
  "text": "第一章 雨夜\n\n正文...\n\n第二章 旧书\n\n..."
}
```

响应示例：

```json
{
  "valid": true,
  "chapter_count": 3,
  "min_chapters_required": 3,
  "message": "成功识别 3 个章节，满足至少 3 章的要求。",
  "preamble": "《城市边缘》\n作者：李四",
  "chapters": [
    {
      "chapter_number": 1,
      "title": "雨夜",
      "heading": "第一章 雨夜",
      "content": "...",
      "char_count": 256,
      "paragraph_count": 8
    }
  ]
}
```

支持的章节标题格式：

- 中文：`第一章 标题`、`第1章 标题`
- 英文：`Chapter 1 Title`

### LLM 状态与测试（PR-05）

`GET /api/llm/status` — 查看 LLM 是否已配置（不消耗 API 额度）

```json
{
  "configured": true,
  "model": "deepseek-chat",
  "base_url": "https://api.deepseek.com",
  "timeout": 120.0,
  "max_retries": 2,
  "message": "LLM 已配置，可调用 /api/llm/test 进行连通性测试。"
}
```

`POST /api/llm/test` — 发送简短测试请求，验证 API Key 与网络连通性

```json
// 请求（prompt 可选）
{ "prompt": "请只回复：OK" }

// 响应
{
  "model": "deepseek-chat",
  "prompt": "请只回复：OK",
  "reply": "OK"
}
```

### 单章场景切分（PR-06）

`POST /api/scenes/split-chapter` — 将单章小说正文拆解为场景列表（调用 DeepSeek）

请求体：

```json
{
  "chapter_number": 1,
  "chapter_title": "雨夜",
  "content": "雨下得很大。林晚合上书，门铃响了..."
}
```

响应示例：

```json
{
  "chapter_number": 1,
  "chapter_title": "雨夜",
  "scene_count": 2,
  "model": "deepseek-chat",
  "scenes": [
    {
      "scene_number": 1,
      "location": "旧时光书店",
      "int_ext": "INT",
      "time": "NIGHT",
      "summary": "林晚与陈野雨夜重逢",
      "characters": ["林晚", "陈野"],
      "source_excerpt": "雨下得很大。林晚合上书..."
    }
  ],
  "characters_mentioned": [
    { "name": "林晚", "role_hint": "protagonist" }
  ]
}
```

### 场景剧本块生成（PR-07）

`POST /api/scenes/generate-script` — 将单个场景生成为含 action_blocks 与 dialogues 的剧本块（对齐 YAML Schema）

请求体：

```json
{
  "act": 1,
  "scene_id": "1-1",
  "chapter_number": 1,
  "chapter_content": "雨下得很大。林晚合上书，门铃响了...",
  "scene": {
    "scene_number": 1,
    "location": "旧时光书店",
    "int_ext": "INT",
    "time": "NIGHT",
    "summary": "林晚与陈野雨夜重逢",
    "characters": ["林晚", "陈野"],
    "source_excerpt": "雨下得很大。"
  },
  "characters": [
    { "id": "char_linwan", "name": "林晚", "role": "protagonist" },
    { "id": "char_chenye", "name": "陈野", "role": "protagonist" }
  ]
}
```

响应示例：

```json
{
  "act": 1,
  "model": "deepseek-chat",
  "scene": {
    "scene_id": "1-1",
    "scene_number": 1,
    "heading": { "int_ext": "INT", "location": "旧时光书店", "time": "NIGHT" },
    "source_mapping": { "chapter": 1, "excerpt": "雨下得很大。" },
    "action_blocks": ["窗外暴雨如注，林晚合上书。"],
    "dialogues": [
      { "character_id": "char_linwan", "line": "欢迎光临。", "emotion": "平静" }
    ],
    "transition": "CUT TO:"
  },
  "characters": [
    { "id": "char_linwan", "name": "林晚", "role": "protagonist" }
  ]
}
```

典型流程：`split-chapter` → 取单个 scene → `generate-script` 生成剧本块。

### 多章转换 Pipeline（PR-08）

`POST /api/convert/novel-to-script` — 一键将 3 章以上小说转换为完整 YAML 剧本初稿

请求体：

```json
{
  "text": "第一章 雨夜\n\n正文...\n\n第二章 旧书\n\n...\n\n第三章 ...",
  "script_title": "雨夜重逢",
  "author": "张三",
  "source_novel_title": "城市边缘",
  "source_novel_author": "李四"
}
```

响应包含：

- `script` — 完整剧本 JSON（meta / characters / acts）
- `yaml` — 可直接保存的 YAML 字符串
- `stats` — 章节数、幕数、场景数、角色数

Pipeline 流程（按章串行）：

1. 解析章节并校验 ≥3 章
2. 每章：场景切分 → 逐场景生成剧本块
3. 跨章合并角色表（同名角色保持同一 ID）
4. 组装为 YAML Schema 结构并导出

### 剧本 Schema 校验（PR-09）

`POST /api/script/validate` — 校验 YAML 或 JSON 剧本是否符合 Schema

请求体（二选一）：

```json
{ "yaml": "schema_version: \"1.0.0\"\nmeta:\n  ..." }
```

或

```json
{ "script": { "schema_version": "1.0.0", "meta": {}, "characters": [], "acts": [] } }
```

响应示例：

```json
{
  "valid": false,
  "errors": [
    {
      "code": "schema",
      "path": "meta",
      "message": \"'meta' is a required property\"
    }
  ],
  "warnings": []
}
```

校验包含两层：

1. **JSON Schema 结构校验**（`schemas/script.schema.json`）
2. **业务规则校验**：scene_id 唯一、对白 character_id 已注册、角色首次出场场景存在等

`POST /api/convert/novel-to-script` 的响应现已包含 `validation` 字段，Pipeline 输出会自动校验。

## 测试

```bash
cd backend
pip install -r requirements.txt
pytest
```

## 文档

- [YAML Schema 定义](docs/yaml-schema.md) — 剧本结构规范与设计说明
- [示例剧本](examples/sample_script.yaml) — 符合 Schema 的完整样例
- [示例小说](examples/sample_novel.txt) — 3 章样例原文（对应示例剧本）
- [JSON Schema](schemas/script.schema.json) — 机器可读的结构校验定义


