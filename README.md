# PPT_agent

制作与优化 PPT 的 AI skill（后续演进为 Agent）。

- **双模式**：熟悉主题就逐页填空；不熟悉主题就先和 AI 头脑风暴，最后汇成同一份逐页大纲。
- **双版本交付**：v1 可编辑 pptx（文本框 + 独立插画，可直接拖动修改）；v2 整页渲染版（美观、跨设备不跑版）。
- **改动闭环（规划）**：在 v1 上改 → 自动识别改动 → 只重渲染受影响页。
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
├── src/                 # M1 校验/组装/辅助导出/检测/生图交接与中文适配
├── fonts/               # 放字体文件（不入库，按 README 下载）
├── assets/              # 生成的背景/插画（不入库）
├── output/              # 产出的 pptx/pdf/png（不入库）
└── specs/               # 每个开发任务的留档（入库）
```

## 第一次使用：环境准备（Windows）

1. 安装 **Python 3.10+**（安装时勾选 Add Python to PATH）。
2. 安装 **LibreOffice**（辅助 PDF/参考图与检查用）：https://www.libreoffice.org/download/ ，配置直接的 soffice.com/exe，不使用会改名的包装脚本。
3. 安装 **Git for Windows**：https://git-scm.com/download/win
4. 在项目目录打开终端，安装依赖：
   ```
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
5. 按 `fonts/README.md` 下载白名单字体，放入 `fonts/`。
6. 依 `.ai/git-workflow.md` 在 feature 分支开发；当前仓库已初始化，无需重复执行初始化脚本。提交通过的检查点，由人类审查后合入。
7. 需要远程协作时，按 `.ai/git-workflow.md` 关联远程仓库；本次样例仅本地分支，未推送。

## M1 当前能力

已确认大纲/风格 → 会话生图生成独立素材 → 单页可编辑 PPT（中文自适应）→ LO 辅助导出及几何/内容检查 → 用户确认 v1 → 生图交接包 → 会话工具整页重绘 → 逐字/数字与视觉核对。

四个本地命令及运行条件见 [src/README.md](src/README.md)。样例执行源为 [m1-input.json](specs/2026-10-18-m1-single-slide/m1-input.json)，开发证据见 [design.md](specs/2026-10-18-m1-single-slide/design.md)。首张正式重绘已生成，正在等待人类视觉验收；不代表阶段 6 或完整 skill 已验收。

最终展示图使用当前会话的 image_gen 工具重绘，底层型号未知；没有独立 API 接入。交付为 v1 PPTX、模型原生 PNG、辅助 PDF/参考图和核对记录。整图 v2 PPTX、多页、自动 diff 与 skill 打包尚未实现；修改 v1 后先人工同步输入再重跑。

## 日常怎么和 AI 协作

开工时对 AI 说：

> 先读 AGENTS.md，按 `.ai/00-workflow.md` 走六阶段流程。现在进入阶段 1，先复述需求并提问，不要写代码。

如果是要让 AI 做 PPT（产品流程），说：

> 按 `.ai/product-sop.md` 开始，先判断我是模式 A 还是模式 B，并逐页确认大纲。

## 关键约束

- 中文文本字号自适应只能用 `src/text_fit.py`，不要用库自带的 `fit_text()`（对中文失效，见 `.ai/knowledge/pitfalls.md`）。
- 不直接使用参考模板里的图片、插画、字体；只提取风格参数。
- 每个开发任务都走 git 分支 + PR，不直接改 main。
