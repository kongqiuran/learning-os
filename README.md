# ExamPilot

48小时生成你的期末冲刺包。

上传老师的 PDF、PPT、讲义、作业，ExamPilot 会自动生成：

- 考点总结
- 公式表
- 题型分类
- 易错点
- 模拟卷
- 7 天复习计划

你不需要懂编程，只要按步骤操作。

Learning OS 是这个项目的仓库名；ExamPilot 是面向学生使用的产品名。

## 适合谁用

- 期末前资料太多看不完
- 不知道老师重点在哪里
- 想快速整理一门课的复习包
- 想用 AI，但不知道怎么提问
- 想把一门课的 PPT、PDF、作业整理成一份可复习的文档

## 入口 A：小白用户版

这一部分适合不会 Git、不会 PowerShell、没装过 Python 的同学。

### 第一步：安装 Python

1. 打开 Python 官网：[https://www.python.org/downloads/](https://www.python.org/downloads/)
2. 点击下载最新版 Python。
3. 安装时一定要勾选 `Add python.exe to PATH`。
4. 一路点击安装即可。

如果你已经安装过 Python，可以跳过这一步。

### 第二步：下载项目 ZIP

1. 打开项目 GitHub 页面。
2. 点击绿色按钮 `Code`。
3. 点击 `Download ZIP`。
4. 下载完成后，右键解压到一个你能找到的位置，比如桌面。

### 第三步：安装依赖

进入解压后的文件夹，第一次使用时双击：

```text
install.bat
```

它会自动安装需要的依赖。

如果窗口里显示：

```text
安装完成，可以双击 start.bat 启动
```

说明安装成功。

### 第四步：配置模型 API Key

在项目文件夹里找到：

```text
.env.example
```

复制一份，改名为：

```text
.env
```

默认推荐使用 DeepSeek，因为国内学生更容易注册和使用。把 `.env` 内容改成：

```env
LLM_PROVIDER=deepseek
LLM_API_KEY=你的 DeepSeek API Key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-v4-flash
```

注意：

- `LLM_API_KEY` 要换成你自己的 Key。
- 不要把 `.env` 发给别人。
- 如果没有 API Key，也可以先启动页面，但不能真正生成复习包。

### 第五步：启动 ExamPilot

以后每次使用，双击：

```text
start.bat
```

启动成功后，浏览器会打开一个本地网页。你只需要：

1. 填课程名称。
2. 上传 PDF、PPTX、TXT 或 MD 资料。
3. 点击“生成期末冲刺包”。
4. 等待生成后下载 Markdown 文件。

生成结果也会保存到：

```text
data/outputs/
```

## 如何使用 OpenAI 或其他模型

ExamPilot 支持任何兼容 OpenAI Chat Completions API 的模型服务，不只支持 OpenAI。

### DeepSeek 默认配置

```env
LLM_PROVIDER=deepseek
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-v4-flash
```

### OpenAI 可选配置

```env
LLM_PROVIDER=openai
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
```

### 其他兼容服务

```env
LLM_PROVIDER=custom
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://your-provider-compatible-api-url/v1
LLM_MODEL=your-model-name
```

## 常见问题

### 1. 双击 install.bat 后提示找不到 Python

说明电脑还没有正确安装 Python，或者安装时没有勾选 `Add python.exe to PATH`。

建议重新安装 Python，并勾选这个选项。

### 2. 页面打开了，但生成时提示没有配置 API Key

说明还没有创建 `.env` 文件，或者 `.env` 里的 `LLM_API_KEY` 还是占位内容。

请检查 `.env` 文件是否在项目根目录，文件名不要写成 `.env.txt`。

### 3. 上传 PDF 后没有提取到文字

有些 PDF 是扫描版图片，不是真正的文字。V1 暂时不做 OCR。

你可以先把资料转成可复制文字的 PDF、TXT 或 Markdown。

### 4. PPT 里有图片公式怎么办

V1 会提取 PPTX 里的文字，但不会识别图片里的公式。图片 OCR 不是本版本功能。

### 5. 生成结果保存在哪里

默认保存在：

```text
data/outputs/
```

页面上也可以直接下载 Markdown 文件。

## 入口 B：开发者版

如果你熟悉 Git 和命令行，可以这样运行：

```bash
git clone https://github.com/kongqiuran/learning-os.git
cd learning-os
pip install -r requirements.txt
```

复制环境变量文件：

```bash
cp .env.example .env
```

填写 `.env` 后启动：

```bash
streamlit run app.py
```

## V1 范围

当前版本只做最小闭环：

```text
上传课程资料 -> 提取文字 -> 调用模型 -> 生成 Markdown 复习包 -> 下载和保存
```

本版本不包含：

- 登录系统
- 支付系统
- 数据库
- RAG 知识库
- 图片 OCR
- 复杂课程管理后台

## 项目结构

```text
learning-os/
├── app.py
├── install.bat
├── start.bat
├── requirements.txt
├── .env.example
├── data/
│   └── outputs/
├── src/
│   ├── config.py
│   ├── loader.py
│   ├── chunker.py
│   ├── prompts.py
│   ├── generator.py
│   └── exporter.py
└── README.md
```

## React 产品前端（渐进迁移）

Learning OS 正在保留原有 Streamlit 入口的同时，逐步增加面向学生的 React 产品界面。两套界面复用同一套 Python service 和数据库，但维护各自独立的浏览器会话。

### 1. 启动原有 Streamlit

原有入口没有变化：

```powershell
cd "D:\kongqiuran\ai\learning-os"
streamlit run app.py
```

也可以继续双击 `start.bat`。

### 2. 启动独立 API Gateway

先安装 Python 依赖，再启动独立的 FastAPI 入口：

```powershell
cd "D:\kongqiuran\ai\learning-os"
pip install -r requirements.txt
python api_server.py
```

默认 API 地址为 `http://127.0.0.1:8000`，接口文档位于 `http://127.0.0.1:8000/api/docs`。公开部署前请在 `.env` 中设置足够长且随机的 `API_SESSION_SECRET`。

### 3. 启动 React 开发服务器

另开一个终端：

```powershell
cd "D:\kongqiuran\ai\learning-os"
cd frontend
pnpm install
pnpm dev
```

访问 `http://127.0.0.1:5173`。开发服务器会把 `/api` 请求代理到独立 API Gateway。

### 4. 验证前端构建

```powershell
cd "D:\kongqiuran\ai\learning-os"
cd frontend
pnpm typecheck
pnpm build
```

当前 React 版本完成注册、登录、会话恢复、统一布局和 Design System。Dashboard、Course Space、Knowledge 的真实业务数据将在后续阶段接入；页面不会使用虚假课程或学习统计。
