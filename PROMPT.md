这份分片器正在灰度，我总觉得分布不太对，需要你审一遍再全量。
shardprng 是 Python 3 的分片选择库，只用标准库（unittest 跑用例），没有第三方依赖，
自检走 `scripts/check.sh`（`check/` 是固定验收程序，别改）。

README 有「对外保证」8 条和「审查交付物」一节；`shardprng/` 下是完整实现（本次不要改它），
`tests/` 里 14 个用例当前全绿，但它们只覆盖小规模、单线程、连续键。
`repro.py` 是灰度环境抓下来的最小输入。

任务：审一遍这份实现，把违反「对外保证」的地方找出来，结论写进 review/REVIEW.md。
每条结论必须给出：涉及的文件与行号、可执行的最小复现命令、实际观察到的输出、违反了第几条保证；
少一样就不算结论。

验收（scripts/check.sh 是固定验收程序，别改）：
- bash scripts/check.sh 退出码 0，10 个场景全过（format 3 + evidence 3 + coverage 2 + integrity 2）。

约束：
1. 不改 shardprng/、tests/、repro.py、scripts/；不新增源码文件；只写 review/REVIEW.md。
2. 不引入第三方依赖，只用标准库。
3. 证据里的统计脚本不许用系统 `random` 或 `time`；要复现就用固定输入。
4. 只写「违反哪条保证」与证据，不要写你打算怎么改（本轮只做审查）。
