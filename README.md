#AI小说转剧本工具
将小说文本自动转换为结构化YAML剧本初稿，辅助快速完成改编。

##Demo视频

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
| （后续 PR 补充 LLM SDK 等） | AI 调用 | Prompt 与转换流程 |

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
cp .env.example .env   # 按需修改
uvicorn app.main:app --reload --port 8000
```

**前端**

```bash
cd frontend
npm install
npm run dev
```

浏览器访问 <http://localhost:5173>，页面会请求后端 `/api/health` 验证连通性。

## 文档

- [YAML Schema 定义](docs/yaml-schema.md) — 剧本结构规范与设计说明
- [示例剧本](examples/sample_script.yaml) — 符合 Schema 的完整样例
- [示例小说](examples/sample_novel.txt) — 3 章样例原文（对应示例剧本）
- [JSON Schema](schemas/script.schema.json) — 机器可读的结构校验定义


