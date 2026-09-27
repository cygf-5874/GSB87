# shardprng

一个**分片选择**小库：把任意 `bytes` 键稳定地映射到 `shards` 个分片之一，
并提供分布统计与分片数变更时的重映射。

```python
from shardprng import shard_of, histogram

shard_of(b"user-42", 8)          # -> 0..7 之间的分片号
histogram([b"a", b"b", b"c"], 4) # -> [{"shard": 分片号, "count": 键数}, ...]
```

## 目录

```
shardprng/__init__.py   对外入口
shardprng/seed.py       种子派生与字节混合
shardprng/bucket.py     分片选择与分布统计
shardprng/rebalance.py  分片数变更时的重映射
tests/test_shardprng.py 既有用例（14 个；只覆盖小规模、单线程、连续键）
repro.py                灰度环境抓下来的一段最小输入
scripts/check.sh        固定验收入口（勿改）
check/check.py          固定验收程序（勿改）
review/CHECKLIST.md     审查核对表（勿改）
review/REVIEW.md        审查结论（待填；本任务的交付物）
```

## 语言版本前提

- Python 3（开发与验证用 3.13）。
- **只用标准库**（`unittest` 等），不引入任何第三方依赖。

## 怎么跑

```bash
python3 -m unittest discover -s tests   # 既有用例，当前 14/14 全绿
python3 repro.py                        # 灰度最小复现
bash scripts/check.sh                   # 固定验收；支持 -list 与 --only <组名>
```

`tests/test_shardprng.py` 只覆盖小规模、单线程、连续键的正常路径。

## 对外保证

下面 8 条是 `shardprng` 的**对外契约**，实现必须全部守住；它们是本题验收点的唯一出处。

1. **均匀**：`shard_of(key: bytes, shards: int) -> int` 必须把键分得均匀 —— 对 10 万个连续键，
   最大桶与最小桶的计数差 ≤ 3%（相对每片平均键数）。
2. **相邻种子不相关**：把 `seed` 从 0 递增到 15 得到的 16 条分片序列，两两之间的重合率
   （同键落同一分片的比例）必须 ≈ `1/shards`，偏差 ≤ 3%。
3. **换分片数只搬动必要的人**：`shards` 从 N 变到 N+1 时，只有约 `1/(N+1)` 的键换桶
   （一致性哈希性质）。
4. **与分配顺序无关**：同样的键集合，无论按什么顺序调用，每个键的分片结果相同。
5. **跨进程一致**：同一进程内多次调用、以及跨进程（不同 `PYTHONHASHSEED`）结果必须一致。
6. **纯函数**：不读写全局可变状态、不用 `time`、不用系统 `random`；同一 `(key, shards)` 恒同结果。
7. **边界**：`shards <= 0` → `ValueError`；空 `key` 是合法输入（不得特殊对待成固定桶）；
   超长 `key`（1 MiB）不得显著慢于短键（分片必须先把 key 摘要成定长）。
8. **分布统计可复现**：`bucket.histogram(keys, shards)` 的输出在固定输入下逐字段稳定。

## 审查交付物

要交出一份 `review/REVIEW.md`，其中**每条结论**都必须写全四要素，缺一样就不算结论：

- 涉及的文件与行号；
- 可直接执行的最小复现命令；
- 实际观察到的输出；
- 违反了上面第几条保证。

## 固定验收

`bash scripts/check.sh` 是固定验收入口，只校验 `review/REVIEW.md` 的交付格式、可执行证据、
对上述 8 条保证的覆盖，以及不可改文件的 SHA-256 基线与文件清单。
**`check/`、`scripts/`、`shardprng/`、`tests/`、`repro.py`、`review/CHECKLIST.md`、本文件一律勿改。**
