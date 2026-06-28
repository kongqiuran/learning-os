# Learning OS

Learning OS 是一个 AI 课程复习包生成器。

它的目标很简单：把课程 PDF、PPT、讲义、作业等资料整理成一份可以直接交付的期末复习包，包括：

- 考点总结
- 公式表
- 题型分类
- 易错点
- 模拟卷
- 7 天复习计划

第一版先做最小可用产品：不追求复杂网页和账号系统，先跑通“课程资料 -> AI 复习包 -> Markdown 下载”的完整流程。

## 适合场景

- 帮同学整理期末复习资料
- 给一门课生成考前复习包样品
- 做课程资料整理服务的交付工具
- 后续扩展成个人学习系统或课程知识库

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

复制 `.env.example` 为 `.env`，然后填入你的 OpenAI API Key。

```env
OPENAI_API_KEY=your_api_key_here
MODEL_NAME=gpt-4o-mini
```

### 3. 启动网页

```bash
streamlit run app.py
```

打开网页后，上传课程资料，填写课程名称，点击生成，即可得到 Markdown 版复习包。

## 项目结构

```text
learning-os/
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── data/
│   ├── raw/
│   ├── processed/
│   └── outputs/
├── src/
│   ├── config.py
│   ├── loader.py
│   ├── chunker.py
│   ├── vector_store.py
│   ├── prompts.py
│   ├── generator.py
│   └── exporter.py
├── templates/
├── examples/
└── docs/
```

## V1 功能

- 支持上传 PDF、PPTX、TXT、Markdown
- 自动提取课程资料文字
- 自动生成中文期末复习包
- 支持 Markdown 下载
- 本地保存输出结果到 `data/outputs/`

## 后续计划

- 支持图片 OCR
- 支持导出 PDF
- 支持按章节生成复习包
- 支持 ChromaDB 本地知识库
- 支持“只根据课程资料回答”的问答模式
- 增加更多样品案例

