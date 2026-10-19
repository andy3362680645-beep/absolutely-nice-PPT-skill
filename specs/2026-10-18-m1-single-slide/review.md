# 审查报告 · M1 单页生图展示链路

> 2026-10-19，阶段 6。代码、视觉、版权三类自审通过；1 个阻塞项已在第一轮修复，未遗留阻塞项。等待人类审查合入，尚未完成阶段 6 的合入质量门。

## 分支与范围

- 分支：`feat/m1-single-slide`。审查起点 `6c0270c`，修复后代码版本 `e2b34f7`；后续收尾提交仅同步本报告与状态说明。
- 当前没有 `main` 引用或远程地址。增量对照首个骨架/验证基线 `2a84b12`，同时完整阅读当前 src 实现，未把初始提交中的中文适配修改排除在审查之外。
- 关联：[spec.md](spec.md)、[design.md](design.md)、[生图核对记录](image-redraw-checklist.md)。
- 实现范围：src 下 config/outline/text_fit/builder/render/checks/m1，入口说明；本任务大纲、风格、JSON、spike 与证据索引；设计列出的产品流程、可行性/编码/审查规范、架构与踩坑记录、根 README。新增本报告是阶段 6 规定产物。
- 本报告由当前会话按清单自审，未冒称独立会话或远程 PR/CI 审查。未创建远程、推送、建立主线或合并。

## 检查点结果（真实执行）

审查复跑使用单独目录，正式已验收产物保持不变：

```powershell
.venv/Scripts/python.exe -X utf8 -m src.m1 build --input specs/2026-10-18-m1-single-slide/m1-input.json --out output/m1-single-slide/review-20261019
.venv/Scripts/python.exe -X utf8 -m src.m1 check --input specs/2026-10-18-m1-single-slide/m1-input.json --out output/m1-single-slide/review-20261019
.venv/Scripts/python.exe -X utf8 specs/2026-10-18-m1-single-slide/spike_text_fit.py
.venv/Scripts/python.exe -m compileall -q src
git diff --check 2a84b12..HEAD
```

| 检查项 | 实际结果 | 证据 |
|---|---|---|
| 构建、重开、原生对象 | passed=true；1 页、15 元素；13 文本框＋2 独立图片 | 审查 run `20261019T004402Z-aa5fbc36` 的 PPTX、manifest |
| LibreOffice 实际转换 | passed=true；PDF/PNG 生成成功 | 同 run 的 `render-3c83c0e1/` |
| 内容、字号、字体与几何 | issues=[]；SourceHanSansSC-Regular/Bold；正文 18pt、页脚 12pt | 同 run checks.json；参考 PNG 与正式 v1 参考图哈希完全一致 |
| 中文边界 | passed=true；9 项断行/宽度＋4 项字号检查 | spike_text_fit.py 实际输出；compileall 无错误 |
| PPTX 基础结构 | 41 个 XML/关系文件可解析；42 个内部关系目标有效；ZIP/内容类型覆盖引用有效 | 审查目录 package-and-provenance.json；不是 XSD 校验 |
| 失效验收复用负例 | 缺图、改核对记录、改提示词、改文案清单、改交接包均拒绝，state=failed | 隔离副本核查；review-evidence.json 汇总 |
| 有效已验收状态复用 | passed=true、state=accepted、reused=true；证据文件只读，哈希未变 | 正式版本复用核查 |
| 最终展示图 | 13 项文案/数字目视核对通过，人类已确认；1672×941，比例误差约 0.0531% | 正式 image-review.json、原图、会话确认 |
| 字体/素材来源 | 2.005R 字体与 OFL 文本哈希一致，两个 AI 素材哈希一致，无字体本体内嵌到 PPTX | fonts/README.md、来源记录、基础结构检查 |
| 入库与源码范围 | 无生成图、PPT/PDF、字体本体、环境入库；未发现源码硬编码密钥/个人路径 | git ls-files、源码扫描；diff --check 无错误 |

本地证据汇总：[review-evidence.json](../../output/m1-single-slide/review-20261019/review-evidence.json)、[package-and-provenance.json](../../output/m1-single-slide/review-20261019/package-and-provenance.json)。这些生成文件按规则不入库。

## 代码检查

### 阻塞项：已清零

- **R1 [P2] 最终图缺失仍返回 accepted，已修复。** 复现：复制已验收运行至临时目录，删除最终图后调用 prepare_image，旧代码返回 passed=true、state=accepted、final_image_exists=false。第一轮修复在 m1.py 对已生成/待验收/已验收阶段校验原交接包、准确文案、提示词、实际提交提示词、最终图与绑定哈希的验收记录；合法版本只读复用，证据改变明确失败，不再重写历史交接或沿用 accepted。五类负例与合法正例均通过，正式图像未改变。
- 中文均走 text_fit，超量失败；原生文本与图片独立。PPTX、输入、素材/字体、检测与参考导出之间以哈希绑定；准备生图前须记录已有的人类确认。
- 本地代码只准备输入包；实际模型调用由会话完成。没有独立 API、OCR、多页自动 diff 或完整 skill 的虚假能力声明。

### 非阻塞建议/验证边界

- **N1** 额外 OOXML XSD 验证器缺少 defusedxml，未运行。已有重开、真实 LO 转换、XML/关系与内容/几何检查，不声称 XSD 通过。后续如引入验证器依赖，按流程单独确认与验证。
- **N2** 未声称实际在 WPS/PowerPoint 中打开测试；可编辑性通过原生对象读回及 LO 验证。交付 v1 仍依赖目标设备具备登记字体。
- **N3** Pillow/PyMuPDF 的依赖声明为范围，跨机器复现前建议记录并核验版本；本次实际版本与阶段 5 证据一致，不在本任务外扩依赖锁定方案。

## 视觉检查（逐页）

| 页码 | 内容正确 | 无明显裁切/遮挡 | 字号与字形 | 风格与层次 | 结论 |
|---|---|---|---|---|---|
| v1 第 1 页 | 与大纲及完整句分组一致 | 自动几何通过＋参考图目视通过 | 思源 Regular/Bold；说明 18pt、页脚 12pt | 茶绿数据强调，右侧独立茶饮 | 用户已确认 |
| 模型第 1 页 | 标题/副标题、三个摘要、三组说明、全部限定词/数字/GO 与来源完整 | 目视未见明显裁切/遮挡 | 验收可读性与无衬线气质，不冒称精确字体或 pt 字号 | 纸片数据区、茶叶、杯体/自然投影协调 | AI 初检与用户视觉确认通过 |

正式原图 SHA256：`b50c14eaf8b863dcafe19aaa5aec22bfd2ee751efd723fbf1c427f677e95c8ff`。未裁切、拉伸、缩放或后期补字；最终位图检查未冒用 v1 的几何检测结论。

## 版权与合规检查

- [x] v1 实际使用的思源静态字体在白名单内，官方固定版本来源、OFL 原文与授权留证均有登记，文件哈希匹配。
- [x] 背景、独立茶饮插画与最终重绘均有真实会话生图记录、提示词与文件哈希，没有直接提取参考模板的图片/截图/插画或字体文件。
- [x] PPTX 未内嵌字体本体；字体文件未入库或随产物打包分发。PDF 使用该字体输出，本次核查依据为本地留存官方 OFL 文本。
- [x] 页脚来源与备注 URL 可追溯，保留“近”“超”与统计单位，没有额外免责尾句、制作说明或冒用内部经营数据。
- [x] 未实现受限平台抓取，未复制联名角色、现有海报或品牌 Logo；素材为原创生图记录，不把外部网页图片自动视为可商用素材。

## 发现但未处理（范围外）

- 原 `.ai/templates/review.md` 第 26 行尾随空格未动；本次新增/修改文件空白检查通过。
- Tabbit 路由仍为既有不可用记录；字体证据为保存的官方许可原文及其忠实渲染，不冒称网页截图。
- requirements.txt 的旧 HTML 阶段注释未改，实际流程与运行文档已同步模型路线，未启用该注释中的 Playwright 依赖。该文件不在本任务修改清单内。

## 结论与本地合并请求

三类自审通过，阻塞项清零，允许交人类意图级审查后合入。**合入质量门尚待人类执行，阶段 6 未标记全部完成。**

建议合并说明：

> 跑通喜茶年度营销单页：从确认大纲与原创独立素材生成可编辑 v1，完成中文适配和真实内容/字体/几何检查，再通过会话生图工具参考原页整页重绘，保留准确文案与来源。补充可追溯交接、验收状态及失效证据保护。当前范围为维护者本机单页，不包含多页、自动 diff、独立生图 API 或整图 v2 PPTX。

当前尚无 main/远程，建议首次本地主线以 `2a84b12` 为骨架基线，再合并已审查分支。以下供**人类审查后执行**，AI 未执行建主线或合并：

```powershell
git status --short
git diff 2a84b12..feat/m1-single-slide -- src
# 确认工作区干净、代码与本报告相符后，首次建立 main：
git branch main 2a84b12
git switch main
git merge --no-ff feat/m1-single-slide -m "merge: M1 单页生图展示链路"
```

本任务没有推送请求。主线合入后再按 06-retrospective.md 执行正式知识蒸馏；实现与修复时已同步的坑记录保留，未提前声称合入完成。
