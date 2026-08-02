# AGENTS.md — dca-proj Git / GitHub 协作约定

> 本文件汇总本仓库的 Git / GitHub 协作约定,是所有协作者(含 AI 助手)提交代码时必须遵守的规范。
> 约定从各 Day 指南、报告模板、README 中提炼;如有冲突,以本文件为准。

---

## 一、仓库与协作模型

- 主仓库 `<owner>/dca-proj`,主分支 `master`,权限 Private(仅限项目参与者)。
- 学生先 Fork 主仓库到自己账户,再 Clone 到本地;不直接 push 主仓库。
- 所有改动走 Pull Request:在自己的 Fork 里开分支 → push → 发起 PR → 导师审阅 → 合并。
- PR 是对话,不是提交按钮:发起 PR = "我准备好了,请检查";审阅意见在 PR 里讨论,通过后才合并进主线。

## 二、提交规范

- 提交信息格式:`type(scope): 中文描述`。
  - type:`feat` / `fix` / `docs` / `style` / `refactor` / `chore`。
  - scope:影响的目录或天数,如 `Day9`、`Day8/Day9`。
  - 示例:`feat(Day6): 完成工具和报告`、`style(Day8): 排版拆分长段落`。
- 一个 commit = 一个完整的变更单元;commit message 说清楚做了什么。

## 三、Pull Request 规范

- 一个 PR = 一个完整的任务,只包含本次(当天)相关文件,不混入其他天的改动。
- 一个 PR 原则上只有一个 commit;多次 commit 在提 PR 前合并(squash)成一个。
- PR 描述写清楚:做了什么、为什么、如何验证。
- 验收以对应报告模板的「提交前检查」节为准;指南不另列清单,避免两份清单打架。
- 学生不直接 push 到 `master`;AI 助手同理,除非导师明确指示。

## 四、提交前检查

- 查文件列表,确认没有无关文件:`git diff --name-only origin/master`。
- 查 commit 历史,确认只有一个 commit:`git log origin/master..HEAD --oneline`。
- 每次提交都检查 `README.md` 是否需要同步更新(如文件结构、工具清单有变动),保持 README 与仓库实际一致。

## 五、数据文件与版本

- 数据文件统一放在 `data/` 目录,每次更新后随代码一并提交到 GitHub,保持线上为最新版本。
- 文件版本历史由 Git 提交记录管理,主文件不在文件名里堆版本号;查看历史用 `git log`。
