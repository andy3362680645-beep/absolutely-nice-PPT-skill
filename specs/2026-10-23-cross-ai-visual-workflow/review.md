# 本轮执行与检查记录

> 当前仍在阶段5。本文件先保存实际检查证据，阶段6再形成最终代码、视觉、版权审查结论。

## 先给人看的进度

完整制作顺序、课堂图解与其他场景的规则、独立谢谢页和重点标注已写入入口及模板。独立检查器可以核对实际PPT和辅助PDF，发现小字号、越界和结构问题，未知项单独列出。

已按确认的大纲/风格生成原创素材与4页可编辑稿，真实导出与客观检查通过，AI已逐页看图。当前v1已获人类明确确认；新版独立包已通过静态与隔离入口检查。四页模型图已实际生成并逐页核对，目前等待人类最终视觉确认；阶段6验收尚未开始。

## 实际确认范围

- 维护者在设计呈现后回复“继续推进”：确认design并进入阶段5。
- 问答“认可大纲与风格，继续制作样张”：仅确认4页内容/风格。
- 问答“认可，沿用此插画风格”：确认第一张素材的线稿、蓝青色与教学插画方向。
- 用户明确回复“认可当前可编辑版，继续整页模型美化”：确认当前v1与其入包，确认绑定PPT的SHA256；模型最终图仍另行验收。

## 检查点真实输出

| 门 | 实际运行与结果 | 当前结论 |
|---|---|---|
| A 对象探针 | probe-01/result.json：passed=true，显式26pt、段落继承24pt、表格22pt、图表标签18pt；未知继承null | 通过 |
| A 中文强调 | emphasis-01受沙箱临时字体加载限制，未导出；允许该临时加载后emphasis-02退出0，passed=true、2个可编辑runs、30pt、全文/边界通过，PDF使用SourceHanSansSC-Regular/Bold | 通过，保留首次失败记录 |
| B 审查正反例 | auditor-regression-01及02退出0；缺PDF/漏角色/未知继承为requires_review，错哈希/混放/小字/越界为failed，真实PDF正例passed | 通过 |
| C 入口校验 | 当前项目及捆绑Python缺少可选validator的PyYAML；使用已有系统Python运行同一quick_validate.py，输出Skill is valid!，未新增依赖 | 通过 |
| C/D 文档 | git diff --check针对SKILL、README、.ai、src退出0；有Git LF/CRLF提示，无格式错误；五个新增Python/探针文件ast.parse通过 | 格式与语法通过，语义按对照清单检查 |
| E M1兼容 | fresh m1-regression-01 build退出0：1页15对象；check退出0，passed=true、issues=[]、实际PDF为思源Regular/Bold | 通过；新运行停在awaiting_v1_confirmation，不写旧accepted |
| F v1样页 | sample-01：4页，真实LO导出后technical_status=passed、errors=[]、needs_review=[]；AI实际查看四张完整预览 | 客观/AI视觉通过，人类v1已明确确认 |
| G 发布阻断负例 | 对未获v1确认的样页执行build，退出1，提示“样页尚未完成客观、视觉与人类v1确认” | 正确拒绝；未生成该负例版本 |

## 代码与范围

- 新模块：src/presentation_audit.py、src/release.py；已确认范围内的规范与模板按design更新。
- src/text_fit.py只改注释/docstring，默认值、参数与算法不变；旧组装/渲染/检查/输入及manifest未改。
- 发布模块使用白名单和暂存目录，旧包不覆盖；正式构建退出0，verify --runtime退出0，49个文件、68处本地引用、ZIP/隐私/原生对象核验通过。系统临时解压在普通沙箱内受限，获准使用系统临时目录后原命令通过，未更改实现。
- 受保护的旧M2、GM记录和上次发布共55个文件，收尾哈希比较changed=[]，全部保持原样。

## 视觉与素材自检

1. 概念页：较大的仓储/运输/交接连续插画，标题、分组和正文层次清楚，重点底纹与原生粗体可编辑。
2. 流程页：不同动作图案，与四个大步骤和解释对应，原生箭头明确顺序。
3. 数据页：原生二维折线图，0/1/2/3/4小时对应2/3/6/4/3℃，坐标0至8，解释在右侧，明确排版演示记录。
4. 谢谢页：独立末页，只有致谢、交流邀请与原创插画，无评价/总结/图表混放。

所有正式插画与背景均为本轮实际image_gen输出，保留原生文件、透明通道、实际尺寸及提示词，底层型号记unknown。没有搬用参考照片、模板图或字体文件。必要概念依据与网上参考实际查看范围已记录于样页大纲，来源在对应页/备注。

## 未完成及发现但不碰

- 四页模型图已生成并核对，待人类确认效果；不将AI自检等同于人类最终验收。
- 新包build、verify --runtime已经通过；篡改、漏文件、ZIP混入文件与覆盖负例均被正确拒绝，旧ZIP哈希未变。独立核验仅覆盖当前环境入口和对象读取，未代替接收方安装或豆包试跑。
- 豆包端尚未实际试跑，兼容性保持待验证。
- M1旧prepare-image固定茶饮提示词、原M2未完成任务与GM历史产物不改；用户个人安装副本不改。
- 当前未提交最终阶段6审查、不推送、不合并。

## 发行检查实际命令与结果

- `python -m src.release build --version 2026-10-23-visual-v1 --sample-run output/cross-ai-visual-workflow/sample-01 --out output/releases`：退出0，passed=true，source_and_old_artifacts_unchanged=true。
- `python -m src.release verify --folder output/releases/ppt-agent-2026-10-23-visual-v1/ppt-agent --zip output/releases/ppt-agent-2026-10-23-visual-v1/ppt-agent-2026-10-23-visual-v1.zip --runtime`：退出0，5项runtime_smoke均exit_code=0。
- 系统已有Python运行PPTX技能的`office/validate.py`检查当前editable.pptx：退出0，All validations PASSED!；未安装新依赖。
- 负例与保护结果：`output/cross-ai-visual-workflow/release-negative-results.json`，passed=true。
- 可交付文件夹与ZIP在新版本目录，未改个人安装副本。包内含人类已确认v1及其参考预览；最终模型图片单独交付。

## 四页整页模型协调结果

使用内置image_gen真实调用，分别输入当前页可编辑预览、相关原创素材、背景和准确文字。第1页先验证，再制作第2至4页。四张均为1672×941原生输出，未用代码覆盖文字、裁剪或拉伸。提示词、哈希和逐页记录保存在`output/cross-ai-visual-workflow/sample-01/model/`。

- 第1页：仓储、运输、交接分别对应主体图示，正文、重点与来源完整。
- 第2页：四组不同动作、四个步骤及对应解释完整，阅读顺序明确。
- 第3页：五点值2/3/6/4/3，与0至4小时及纵轴0至8对应，重点说明与“排版演示记录”完整。目视核对关系，不宣称OCR或像素精确检测。
- 第4页：独立谢谢页，仅致谢、交流邀请、页码与原创人物。

AI视觉自检通过，人类模型图确认pending，尚未进行阶段6代码/视觉/版权联合验收，未合并。

## 最新人类反馈：风格认可，信息量需修订

用户认可四页图片风格，但指出第3页文字与分析过少，学术/文献场景需要充分论证。此回复不作为最终模型验收。当前阶段5退回受影响内容/版式，补充方案见academic-density-revision.md；尚未修改正式规则、样页代码或发行快照。原包仅为本轮反馈前的候选版本，不作为最终完成版推荐。

## 学术密度修订已实施，待确认新版可编辑稿

维护者明确认可补充方案与第3页大纲。已更新入口、产品流程、文献/视觉约定、大纲/跨宿主模板和视觉审查要求：学术页保留必要论证，不统一限为几个短句，既检查堆字也检查信息过薄。

第3页新增记录特征、分析思路和证据边界三组解释，原生图表不变；标题40pt、分组26pt、三段正文24pt。查看真实整页预览后，AI认为内容充分且层级清楚，暂无溢出/遮挡问题。仍为讲解演示，不是论文实证。

实际检查：

- 新版构建命令：`python specs/2026-10-23-cross-ai-visual-workflow/build_visual_sample.py --brief output/cross-ai-visual-workflow/sample-brief-academic-v2.md --assets assets/cross-ai-visual-workflow/sample-01 --out output/cross-ai-visual-workflow/sample-academic-02`，退出0；4页，technical_status=passed，errors=[]，needs_review=[]。
- 系统Python运行PPTX技能office/validate.py检查新版editable.pptx：退出0，All validations PASSED!。
- quick_validate.py检查skill：退出0，Skill is valid!。git diff --check针对本轮文件退出0。
- 7份修改规则的45处本地引用/锚点核对通过，55个历史受保护文件无变化。
- 第1、2、4页的slide XML和参考PNG逐字节相同，未改其内容或重新制作素材；记录见新版revision-check.json。

新版运行目录：`output/cross-ai-visual-workflow/sample-academic-02/`，旧sample-01与原包保留。新版v1的人类确认pending；尚未重渲染第3页或构建新版发行包。当前仍在阶段5，不推送、不合并。
