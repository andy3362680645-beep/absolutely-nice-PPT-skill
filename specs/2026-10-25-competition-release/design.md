# 技术方案 · 参赛公开技能包发布

> 阶段 4 产出。人类确认前不得执行正式构建。

## 方案概述

- 版本名固定为 `2026-10-25-competition-v1`，最终目录为 `output/releases/ppt-agent-2026-10-25-competition-v1/`，上传文件为其中同名 ZIP。
- 为使包内清单准确标注已合并且无未提交变更的源码，使用当前仓库创建一个指向 `origin/main` 提交 `923f96accf84e2f56717cf2c8a508332f9bd6e69` 的临时 detached Git worktree；构建完成并双重验证后，把完整版本目录复制到主工作区的 `output/releases/`，再删除临时 worktree。
- 只调用现有 `src.release`，不修改程序、公共规则、样例或旧发行包。任务留档在当前 `chore/competition-release` 分支提交，最终 ZIP 仍从干净 main 基线产生。

## 数据结构与接口

- 涉及的输入文件/数据结构：
  - 干净基线：`origin/main` / `923f96accf84e2f56717cf2c8a508332f9bd6e69`。
  - 构建入口：`python -m src.release build --version 2026-10-25-competition-v1 --sample-run <绝对样例目录> --out output/releases`。
  - 样例证据：`output/cross-ai-visual-workflow/sample-academic-02/`，由构建器重新核对 `sample-record.json`、`audit.json`、PPTX 与四张 PNG 的哈希。
  - 发布清单：包内 `release-manifest.json`，沿用 schema 1，不新增字段。
  - 验证入口：`python -m src.release verify --folder <发布文件夹> --zip <ZIP> --runtime`。
- 新增/修改的函数签名与输入输出：无。只复用 `build_release()`、`verify_release()`、skill-creator `quick_validate.py` 和既有边界验证脚本。
- 文件落点：
  - 公开交付：`output/releases/ppt-agent-2026-10-25-competition-v1/ppt-agent-2026-10-25-competition-v1.zip`。
  - 同目录辅助核验：`ppt-agent/` 文件夹、`build-report.json`。
  - 开发留档：本目录新增 `validation.md`、`review.md`；`output/` 继续不入 Git。

## 实现步骤（按依赖排序，垂直切片）

### 步骤 1：冻结基线与任务记录

- 改动文件：提交当前 `spec.md`、`design.md` 到 `chore/competition-release`；不改公共 skill 文件。
- 动作：重新获取远程引用，确认 PR #3 已合入且 `origin/main` 仍为计划提交；确认目标版本目录不存在；记录旧发行目录的文件路径、大小与 SHA-256 快照，确认个人偏好未被 Git 跟踪。
- 检查点 A：
  - `git rev-parse origin/main` 等于设计基线；若远程 main 已变化，停止并回阶段 4 重新确定基线。
  - `git status` 仅含本任务允许的留档变化。
  - `git ls-files -- .local` 无输出；目标版本目录不存在。

### 步骤 2：从干净 main 构建候选发布包

- 改动文件：只在 `output/` 下创建临时 detached worktree及其候选发布目录。
- 动作：在 `output/.competition-release-source-923f96a/` 创建指向既定 main 提交的临时 worktree；确认该 worktree Git 状态干净；使用项目现有 `.venv` Python 从临时 worktree运行 `src.release build`，样例目录使用主工作区绝对路径。
- 检查点 B：
  - 构建命令退出 0，返回 `passed: true`。
  - 候选 `release-manifest.json` 的 `source_revision` 等于既定提交，`source_has_uncommitted_changes` 为 `false`。
  - 候选目录、ZIP、`build-report.json` 均存在，旧发布目录哈希未变化。

### 步骤 3：候选包完整验证

- 改动文件：无；验证仅生成临时目录或检查输出。
- 动作：对候选运行 `src.release verify --runtime`；以隔离 PyYAML 依赖运行 skill-creator `quick_validate.py`；运行既有 `verify_release_boundary.py` 的真实包验证；额外检查 ZIP 顶层、体积、关键规则、清单与隐私边界。
- 检查点 C：
  - 仓库验证器报告文件、相对链接、ZIP 完整性、隐私扫描、样例结构和 5 项隔离运行全部通过。
  - skill-creator 输出 `Skill is valid!`。
  - ZIP 全部条目都位于唯一的 `ppt-agent/` 顶层；大小小于十进制 `100,000,000` 字节。
  - 包内 `SKILL.md`、`literature-report.md`、`deck-outline.md`、`wireframe-layouts.md` 与干净基线对应文件一致，并存在“先讲清论文的叙事与页间关系”规则。
  - 包内不存在 `.local/`、`specs/`、任务 `output/`、用户论文/PPT、GM 乳业成果、字体本体、Git 元数据或私有路径/身份模式。

### 步骤 4：原子式发布到正式输出目录并复验

- 改动文件：新增 `output/releases/ppt-agent-2026-10-25-competition-v1/`；不覆盖任何既有目录。
- 动作：在确认正式目标仍不存在后，复制整个已验证版本目录；对正式位置再次运行 `src.release verify --runtime` 和关键内容检查；计算最终 ZIP 字节数、易读大小和 SHA-256。
- 检查点 D：正式位置与候选位置逐文件哈希一致；正式 ZIP 全部检查再次通过；旧发布包哈希与步骤 1 快照一致。

### 步骤 5：清理临时构建源并留档

- 改动文件：删除本任务创建的临时 worktree；新增 `validation.md`，阶段 6 再新增 `review.md`。
- 动作：使用 Git worktree 命令移除确切临时路径并 prune；确认最终发布目录仍存在且可打开；把实际命令、退出码、基线、文件数、体积、SHA-256 和边界说明写入人类可读记录。
- 检查点 E：临时 worktree已从 `git worktree list` 消失；当前开发工作树仅含本任务留档；最终 ZIP 不受清理影响。

## 专项检查（必须逐条回答）

1. 中文文本：本任务不制作或修改 PPT 文本，不调用 `fit_text()`；`src/text_fit.py` 保持原样，因此中文字号与超限规则不适用。
2. 字体一致性：不做 PPT 渲染；发布包明确不携带字体本体，只保留已有字体准备说明。样例 PPTX 由验证器检查不得暗带字体文件。
3. v1/v2：不修改 v1 组装、v2 模型图或共用内容数据，只发布现有公共 skill 快照。
4. 改动识别：不涉及原生 PPT diff 或 manifest 变更；`release-manifest.json` 仅记录发布文件路径、大小、哈希和源码状态。
5. 素材生成：不调用生图工具、不新增图片。只复用此前已确认的四页原创公开样例及参考 PNG。
6. 版权：不复制外部模板、真实产品图或字体；样例和公共文档沿用已审查范围。赛事包没有新增许可证或转授权声明。
7. spike：无需新 spike。现有发布路径已实际跑通；本次必须重新执行全部真实检查，旧报告不能替代新包证据。

## 关键决策与备选

| 决策点 | 选择 | 备选 | 取舍理由 |
|---|---|---|---|
| 构建源码 | 干净的 detached `origin/main` worktree | 当前任务分支直接构建 | 当前分支含任务留档，会令清单标记源码有变化；干净 main 更适合参赛发布和复现。 |
| 版本名 | `2026-10-25-competition-v1` | 覆盖 `wireframe-v1` 或沿用其名称 | 新名称能明确区分旧包，且发布器本身禁止覆盖。 |
| 公开内容 | 沿用发布器白名单及已确认样例 | 手工压缩整个仓库 | 白名单能排除个人偏好、任务产物、字体、Git 和环境文件，风险更低。 |
| 最终落点 | 复制验证通过的完整版本目录到主工作区 `output/releases` | 只留下临时构建目录 | 稳定路径便于用户选择文件，且不受临时 worktree 清理影响。 |
| 上传动作 | 本轮只交付本地 ZIP 和路径，由用户在赛事网页选择上传 | AI 直接操作赛事网页 | 用户当前只问应上传哪个文件；网页提交可能包含参赛承诺与其他表单，不扩张授权。 |

## 找茬自审（每个关键决策至少 2 个可能出错点）

- 风险 1：远程 main 在构建前发生变化，包的来源与设计不一致。→ 应对：步骤 1 再 fetch 并严格比较提交；不一致即回阶段 4，不悄悄换基线。
- 风险 2：临时 worktree位于 `output/`，清理时误删正式发布目录。→ 应对：临时路径与最终路径固定且不同；仅用 `git worktree remove` 针对经 `git worktree list` 核实的确切临时路径，不使用通配符或递归删除命令。
- 风险 3：外部样例目录不在临时 worktree保护快照内。→ 应对：构建器会逐项核验样例记录和哈希；构建前后另对样例九项证据做 SHA-256 快照比较。
- 风险 4：包通过自身清单检查但仍是旧内容。→ 应对：把四个关键公共文件与既定 main 基线做逐文件哈希比较，并检查新增叙事规则锚点。
- 风险 5：赛事平台按十进制 100 MB 限制，而操作系统显示二进制 MB。→ 应对：以更严格的 `100,000,000` 字节为硬上限，同时报告原始字节数和 MiB。
- 风险 6：发布包含用户身份、私人风格或 GM 项目资产。→ 应对：发布器路径白名单与内容正则双检，另枚举 ZIP 条目和关键词；个人文件保持 `.local/` 且未被 Git 跟踪。
- 风险 7：复制候选到正式目录时内容发生变化或遗漏。→ 应对：复制后再跑完整 verify，逐文件比较候选与正式目录哈希，最终只引用正式 ZIP。
- 风险 8：skill-creator 校验依赖当前项目未安装的 PyYAML。→ 应对：复用此前已经验证的隔离依赖目录 `output/wireframe-validation-deps`，仅为该验证进程设置 `PYTHONPATH`，不修改项目或全局依赖。

## 待确认问题（清零后才能编码）

- 无。版本名、基线、公开边界、检查点和最终落点均已确定。

## 人类确认

- 确认人：Andy Mao（会话回复“继续”）。
- 日期：2026-10-25。
