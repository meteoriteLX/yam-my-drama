## AI 小说转剧本工具

将小说文本自动转换为结构化YAML剧本初稿，帮助快速完成小说到剧本的改编。

## Demo 视频

- Demo 链接：<https://share.weiyun.com/ivFXuSaq>

## 功能介绍

- **章节解析**：自动识别小说中的章节结构，并校验是否满足至少 3 章的要求。
- **场景切分**：按章拆分为多个场景，辅助把小说叙事转换为剧本结构。
- **剧本生成**：将场景转换为结构化剧本块，生成可编辑的 YAML 初稿。
- **异步转换**：支持后台任务执行，页面实时展示转换进度。
- **在线编辑**：支持直接编辑生成后的 YAML 内容。
- **导出与复制**：支持复制 YAML、下载 `.yaml` 文件。
- **样例体验**：内置 3 章样例小说，可一键跑完整流程。

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

| 模块 | 技术                    | 说明                        |
| -- | --------------------- | ------------------------- |
| 前端 | React 18 + Vite 5     | 用户界面与 YAML 编辑             |
| 后端 | Python 3.11 + FastAPI | REST API 与 AI 转换 Pipeline |
| 容器 | Docker Compose        | 本地一键部署                    |

### 第三方依赖

| 依赖                           | 用途                 | 原创部分                           |
| ---------------------------- | ------------------ | ------------------------------ |
| React / React DOM            | 前端渲染与交互            | 业务 UI、进度展示、编辑体验                |
| Vite                         | 前端开发与构建            | 页面集成与样例体验                      |
| FastAPI / Uvicorn            | 后端 Web 框架          | 章节解析、AI Pipeline、异步任务与 YAML 生成 |
| Pydantic / Pydantic Settings | 数据模型与配置管理          | 剧本结构、任务状态、请求校验                 |
| PyYAML / jsonschema          | YAML 导出与 Schema 校验 | 剧本结构验证、错误提示与导出                 |
| httpx                        | HTTP 客户端           | LLM OpenAI 兼容 API 调用（原创封装）     |
| pytest                       | 测试框架               | 后端单元测试与 API 测试                 |

## 快速开始

### 1. 启动后端

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

启动后，后端地址为：`http://localhost:8000`

### 2. 启动前端

```bash
cd frontend
npm install
npm run dev
```

启动后，前端地址为：`http://localhost:5173`

### 3. 打开页面并体验功能

进入前端页面后，可以直接使用以下两种方式：

#### 方式一：一键体验样例

1. 点击 **「一键体验样例」**
2. 系统会自动加载内置 3 章样例小说
3. 页面会自动完成章节解析、异步转换和 YAML 生成
4. 转换完成后，可以直接编辑、复制或下载 YAML

#### 方式二：手动输入小说

1. 在左侧输入框粘贴至少 3 章小说文本
2. 点击 **「解析章节」** 查看章节识别结果
3. 点击 **「开始转换为 YAML 剧本」** 发起转换
4. 等待进度条完成后，在下方查看生成的 YAML，并进行编辑、复制或下载

### 4. 使用 Docker 一键启动

如果你想直接同时启动前后端，也可以执行：

```bash
docker compose up --build
```

随后访问：

- 前端：<http://localhost:5173>
- 后端：<http://localhost:8000>
- API 文档：<http://localhost:8000/docs>

## API 概览

### 章节解析

`POST /api/chapters/parse`

### LLM 状态与测试

`GET /api/llm/status`

`POST /api/llm/test`

### 单章场景切分

`POST /api/scenes/split-chapter`

### 场景剧本块生成

`POST /api/scenes/generate-script`

### 多章转换 Pipeline

`POST /api/convert/novel-to-script`

`POST /api/convert/jobs`

`GET /api/convert/jobs/{job_id}`

### 剧本 Schema 校验

`POST /api/script/validate`

## 文档

- [YAML Schema 定义](docs/yaml-schema.md) — 剧本结构规范与设计说明
- [示例剧本](examples/sample_script.yaml) — 符合 Schema 的完整样例
- [示例小说](examples/sample_novel.txt) — 3 章样例原文（对应示例剧本）
- [JSON Schema](schemas/script.schema.json) — 机器可读的结构校验定义

## 运行与测试

```bash
cd backend
pip install -r requirements.txt
pytest
```

```bash
cd frontend
npm install
npm run build
```

## 开发说明

- 后端接口采用 FastAPI，支持同步转换与异步任务两种方式。
- 前端提供章节解析、转换进度、在线 YAML 编辑、复制与下载能力。
- 内存异步任务队列主要用于 Demo 与单机演示场景，便于在三天实训中快速验证体验。

