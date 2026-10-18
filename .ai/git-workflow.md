# Git 工作流规范（单人 + AI 协作版）

> 目的：main 永远是可运行的；每一次改动都有分支、有提交记录、有审查；改坏了一定能退。
> 读者：人类（仓库主人）与 AI 协作者。AI 必须把本文件当作硬约束执行。

## 1. 两条分支类型

| 分支 | 用途 | 规则 |
|---|---|---|
| `main` | 主线 | 永远保持"拉下来就能跑"；**禁止直接提交**；只接收 PR 合入 |
| `feat/xxx`、`fix/xxx` 等 | 任务支线 | 一个任务一条分支；做完、验过、合入后删除 |

AI 开工第一步必须确认当前分支不是 main；若是 main，先创建任务分支。

## 2. 分支命名

| 前缀 | 用途 | 示例 |
|---|---|---|
| `feat/` | 新功能 | `feat/v2-renderer` |
| `fix/` | 缺陷修复 | `fix/text-overflow-title` |
| `spike/` | 技术验证（不保证产出） | `spike/pptx-diff`、`spike/link-crawler` |
| `chore/` | 环境、依赖、杂项 | `chore/add-libreoffice` |
| `docs/` | 文档规范 | `docs/sop-update` |

命名用小写英文，单词用连字符；任务名与 `specs/` 目录名对应。

## 3. 任务全生命周期（AI 与人类的标准动作）

```
main 上建分支
   │
   ▼
[阶段1-4] 需求访谈 → 可行性 → 勘察 → 方案（人类确认 design.md）
   │
   ▼
[阶段5] AI 在分支上编码，每个检查点通过后提交
   │
   ▼
[阶段6] AI 自测 → 推送分支 → 开 PR（或本地发起合并请求）
   │
   ▼
人类审查 diff（意图级审查，见 .ai/05-review.md）
   │        ┌── 不通过：在 PR 评论，AI 在同一分支修复后再次推送（最多 3 轮）
   └────────┤
            └── 通过：人类合入 main → 删除分支
   │
   ▼
知识蒸馏（.ai/06-retrospective.md）
```

**关键纪律**

- AI 不自行合并 PR；合入按钮只能由人类点击。
- AI 不执行 `git push --force`、`git reset --hard`、`git clean` 等破坏性操作，除非人类明确授权。
- 每次提交前，相关检查点（脚本运行、渲染、视觉自检）必须先通过。
- 一个分支只做一件事；发现范围外问题，记入"发现但不碰"，另开分支处理。

## 4. 提交信息规范（Conventional Commits）

格式：`类型: 简述`

```
feat: 新增 v1 可编辑 pptx 组装器
fix: 修复标题超过 20 字时溢出的问题
spike: 验证 pptx 文本改动可被 diff 识别
docs: 补充字体授权登记说明
chore: 锁定 python-pptx 版本
refactor: 抽出渲染模块公共参数
test: 增加文本溢出几何检测脚本
```

规则：

- 一次提交对应一个完整、可运行的检查点，不要攒一大堆再提交。
- 简述用中文，写清"做了什么"，不写"改了几个文件"。
- 可以用空行补正文，说明为什么这么改。

## 5. 路径 A：远程 PR（推荐，有云端备份）

推荐 Gitee 私有仓库（国内速度快、免费），GitHub 同理。

### 首次配置（只做一次）

```
git remote add origin https://你的仓库地址
git push -u origin main
```

### 每个任务的命令（IDE 终端，或让 AI 执行除合入外的步骤）

```
# 1. 确保在最新 main 上
git checkout main
git pull

# 2. 建任务分支
git checkout -b feat/任务名

# 3. 开发过程中，每个检查点通过后
git add -A
git commit -m "feat: xxx"

# 4. 完成后推送
git push -u origin feat/任务名
```

推送后在 Gitee/GitHub 网页或 IDE 的源代码管理面板点 **"新建 Pull Request / 合并请求"**，用 `.github/pull_request_template.md` 模板填写。

### 人类审查后合入

- 网页上点"合并"（选择普通合并或 squash 均可，单人项目建议 squash，历史更干净）。
- 合入后删除远程分支，本地清理：

```
git checkout main
git pull
git branch -d feat/任务名
```

## 6. 路径 B：本地合并（暂不建远程仓库时的等效方案）

```
# 开发完成、自测通过后，在任务分支上
git checkout main
git merge --no-ff feat/任务名 -m "merge: feat/任务名"
git branch -d feat/任务名
```

`--no-ff` 会保留分支记录，事后能看清"这一批改动属于同一个任务"。

**建议尽早建远程仓库**：本地分支只能防"改坏"，不能防"电脑丢失"。

## 7. 审查 PR 时人类看什么（意图级，不看行级风格）

1. 这个 diff 是否准确实现了 `design.md` 的需求意图？
2. 有没有碰方案外的文件？
3. 检查点结果（运行截图/渲染图/几何检测）是否齐全且通过？
4. 安全与版权：字体白名单、素材来源、无硬编码密钥。
5. 跨模块/关联点是否遗漏（本项目重点：改了文字处理是否同步改渲染、改动识别、v2 生成）。

## 8. 常见场景速查

- **AI 在分支上改坏了、想重来**：
  ```
  git checkout main
  git branch -D feat/坏分支
  git checkout -b feat/新分支
  ```
  （丢弃分支不影响 main；未提交的修改会丢，先确认。）
- **任务做到一半要切去修紧急 bug**：
  ```
  git stash                # 暂存当前改动
  git checkout main
  git checkout -b fix/紧急
  # 修完合入后
  git checkout feat/原任务
  git stash pop
  ```
- **main 上有了新提交，任务分支想同步**：
  ```
  git checkout feat/任务名
  git merge main
  ```
- **不确定当前在哪个分支、改了什么**：
  ```
  git status
  git branch --show-current
  git log --oneline -10
  ```

## 9. 不入库的内容（已在 .gitignore）

- `assets/`、`output/`：生成的图片、pptx、pdf（体积大，可重新生成）。
- `fonts/` 字体本体：体积大，按 `fonts/README.md` 清单下载。
- `.venv/`、`__pycache__/`、`.env`、临时文件。
- 入库的只有：代码、规范、模板、`specs/` 留档、知识库（文本资产）。
