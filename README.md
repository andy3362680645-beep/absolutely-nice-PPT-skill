# PPT_agent

制作与优化 PPT 的 AI skill（后续演进为 Agent）。

- **双模式**：熟悉主题就逐页填空；不熟悉主题就先和 AI 头脑风暴，最后汇成同一份逐页大纲。
- **双版本交付**：v1 可编辑 pptx（文本框 + 独立插画，可直接拖动修改）；v2 整页渲染版（美观、跨设备不跑版）。
- **改动闭环**：在 v1 上改 → 自动识别改动 → 只重渲染受影响页。
- **风格合规**：从参考模板只提取风格参数，所有视觉素材 AI 重新生成，字体只用可商用白名单。

## 目录说明

```
PPT_agent/
├── AGENTS.md            # AI 协作总纲（最高准则，人和 AI 都读）
├── .ai/                 # 流程规范、模板、知识库
│   ├── 00~06-*.md       # 开发六阶段规范
│   ├── git-workflow.md  # git 分支/PR 规范
│   ├── product-sop.md   # 带用户做 PPT 的流水线
│   ├── templates/       # 文档模板
│   └── knowledge/       # 字体、架构、约定、踩坑记录
├── src/                 # 代码（text_fit.py 已就位）
├── fonts/               # 放字体文件（不入库，按 README 下载）
├── assets/              # 生成的背景/插画（不入库）
├── output/              # 产出的 pptx/pdf/png（不入库）
└── specs/               # 每个开发任务的留档（入库）
```

## 第一次使用：环境准备（Windows）

1. 安装 **Python 3.10+**（安装时勾选 Add Python to PATH）。
2. 安装 **LibreOffice**（渲染用）：https://www.libreoffice.org/download/ ，安装时记住安装路径，确保 `soffice` 可被命令行调用。
3. 安装 **Git for Windows**：https://git-scm.com/download/win
4. 在项目目录打开终端，安装依赖：
   ```
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
5. 按 `fonts/README.md` 下载白名单字体，放入 `fonts/`。
6. 双击 **`setup_git.bat`** 完成 git 初始化和首次提交。
7. 按 `.ai/git-workflow.md` 关联远程仓库（推荐 Gitee 私有仓库，国内速度快）。

## 日常怎么和 AI 协作

开工时对 AI 说：

> 先读 AGENTS.md，按 `.ai/00-workflow.md` 走六阶段流程。现在进入阶段 1，先复述需求并提问，不要写代码。

如果是要让 AI 做 PPT（产品流程），说：

> 按 `.ai/product-sop.md` 开始，先判断我是模式 A 还是模式 B，并逐页确认大纲。

## 关键约束

- 中文文本字号自适应只能用 `src/text_fit.py`，不要用库自带的 `fit_text()`（对中文失效，见 `.ai/knowledge/pitfalls.md`）。
- 不直接使用参考模板里的图片、插画、字体；只提取风格参数。
- 每个开发任务都走 git 分支 + PR，不直接改 main。
