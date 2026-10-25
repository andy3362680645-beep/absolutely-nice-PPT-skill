# 阶段 5 验证记录 · 参赛公开技能包发布

日期：2026-10-25  
分支：`chore/competition-release`  
发布版本：`2026-10-25-competition-v1`

## 最终交付

- ZIP：`output/releases/ppt-agent-2026-10-25-competition-v1/ppt-agent-2026-10-25-competition-v1.zip`
- 大小：`11,275,357` 字节（`10.75 MiB`），小于赛事页面的 `100,000,000` 字节硬上限。
- SHA-256：`C7B661B90DB2E3AF9ABE2C2A86D6C253CF2A43C4CB952F6541BD92DB3855B346`
- 包内源码基线：`923f96accf84e2f56717cf2c8a508332f9bd6e69`（PR #3 已合入后的 `origin/main`）。
- 清单源码状态：`source_has_uncommitted_changes=false`。

## 检查点 A：基线与范围

- `git fetch origin` 后 `origin/main` 仍为设计确认的 `923f96a...`。
- 正式目标目录构建前不存在，旧包未被覆盖。
- `git ls-files -- .local` 返回 0 项；个人偏好未被 Git 跟踪。
- 阶段 1～4 留档提交：`f8d6a88c61925efd49d90046cae63bdd5d80cb13 docs: 规划参赛技能包发布`。
- 构建前记录了 4 个旧技能 ZIP 和 7 项样例关键证据的 SHA-256。

## 检查点 B：干净 main 构建

正式候选使用临时 detached worktree运行：

```text
HEAD = 923f96accf84e2f56717cf2c8a508332f9bd6e69
src.release build: passed=true
source_revision=923f96accf84e2f56717cf2c8a508332f9bd6e69
source_has_uncommitted_changes=false
manifest files=52（不含清单自身）
```

第一次命令因没有先切换进临时 worktree，发布器虽返回成功，但清单来源是当前任务提交 `f8d6a88...`。自定义基线断言立即拒绝该包，没有进入正式目录。该无效生成包曾移到 `output/.invalid-competition-release-f8d6a88` 供诊断；正确候选通过后已删除，只删除本任务生成的无效产物，没有删除用户文件或旧发行包。

修正方式：在临时 worktree内运行同一 `src.release build` 命令，并重新检查清单来源与 dirty 状态。修正后一次通过，不修改发布器代码。

## 检查点 C：候选完整验证

`src.release verify --runtime` 实际结果：

```json
{
  "passed": true,
  "files": 53,
  "local_links": 104,
  "zip_integrity": true,
  "privacy_scan": true,
  "sample_editable_structure": true,
  "runtime_smoke": [
    {"module": "src.m1", "exit_code": 0},
    {"module": "src.m2", "exit_code": 0},
    {"module": "src.presentation_audit", "exit_code": 0},
    {"module": "src.release", "exit_code": 0},
    {"module": "src.presentation_audit inventory", "exit_code": 0}
  ]
}
```

- skill-creator `quick_validate.py`：`Skill is valid!`，退出 0。
- `verify_release_boundary.py`：`passed=true`；公共模板保留，合成 `.local/ppt-agent/preferences.md` 与 `.ai/.local/preferences.md` 篡改包均被拒绝。
- ZIP 共 53 个条目，唯一顶层目录为 `ppt-agent/`，禁止路径计数 0。
- 关键文件与干净 main 逐文件哈希一致：

| 文件 | SHA-256 |
|---|---|
| `SKILL.md` | `B245BC421E4CBDF2E197D21A6FFE6BDE40613FDFB9EDBE893A433039A9C503D3` |
| `.ai/knowledge/literature-report.md` | `725CA7338E5314E065DA9C4FB2751A646D591708EDFA7A07AAE86B7FD657DD90` |
| `.ai/templates/deck-outline.md` | `6F095FB5E1C89063DDB0A6977EDFA1A2718228960321B8182F2985A30E739A24` |
| `.ai/knowledge/wireframe-layouts.md` | `AF0391A3513C98E67A6579C2E77F2BE2D88B9DB40994B74C65E7AF031D5764CC` |

- 包内实际存在“先讲清论文的叙事与页间关系”规则。
- 包内无 `.local/`、`.git/`、`specs/`、任务 `output/`、GM 成果目录或字体本体。

## 检查点 D：正式目录复验

- 将完整候选版本目录复制到正式 `output/releases/` 后，再次运行 `src.release verify --runtime`，结果仍为 53 个文件、104 个相对链接、5 项隔离运行全部退出 0。
- 候选与正式目录共 55 个实际文件（包含包文件夹、ZIP、清单和构建报告），逐文件 SHA-256 全部相同。
- 4 个旧技能 ZIP 的 SHA-256 与构建前一致。
- 7 项样例关键证据的 SHA-256 与构建前一致。

## 检查点 E：清理与最终状态

- 临时 detached worktree 已通过 `git worktree remove --force <确切路径>` 移除并 prune；`git worktree list` 只剩当前任务工作树。
- 基线不符的无效新生成包已删除；正式 ZIP 保留且 SHA-256仍为 `C7B661...5B346`。
- 当前 Git 工作树在写入本记录前干净，公共源码和旧发布包没有改变。

## 验证边界

- 本轮验证证明本地 ZIP 结构、内容、隐私边界、样例结构及包内 Python 入口可运行。
- 没有在赛事平台实际上传或解析，因此不声称赛事平台兼容性已经由平台端确认。
- 没有重新安装接收方依赖、导出 PPT/PDF、调用生图模型或在其他 AI 宿主制作 PPT；这些不属于本次打包任务。
