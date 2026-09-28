# 代码审查结论 · shardprng

> 按 `review/CHECKLIST.md` 的格式逐条填写；每条结论都能照抄复现。
> 本文件只写「违反了哪条保证」与证据，不写修复建议。

## 结论清单

### 结论 1

- 保证编号: 1
- 缺陷位置: shardprng/seed.py:42
- 复现命令: `python3 repro.py`
- 实际输出:

```
分片数     = 50
键数       = 100000
最少的一片 = 776
最多的一片 = 3961
最大最小差 = 159.2%（阈值 3.0%）
=> 分布异常
```

- 违反说明: `key_hash` 在 8 条 lane（`shardprng/seed.py:39-43`）上各取一个 0..255 的
  `mix` 值，再取其中的**最大值**（第 42 行 `best = score`）。8 个独立均匀值取 max 会把
  分布严重推向高位，结果在 `% shards` 下严重偏斜。灰度输入本身（10 万个连续键、50 片）
  的最大桶/最小桶差为 159.2%，远超第 1 条保证要求的 ≤ 3%；命令退出码为 1。

### 结论 2

- 保证编号: 1
- 缺陷位置: shardprng/seed.py:29
- 复现命令: `python3 -c "from shardprng import histogram; keys=[b'key-%06d'%i for i in range(100000)]; c={r['shard']:r['count'] for r in histogram(keys,300)}; empty=[s for s in range(300) if c.get(s,0)==0]; print('reachable shards:',sorted(c)[:1],'..',sorted(c)[-1:]); print('empty shard count:',len(empty),'first empties:',empty[:6]); print('min count:',min(c.get(s,0) for s in range(300)),'max count:',max(c.get(s,0) for s in range(300)))"`
- 实际输出:

```
reachable shards: [52] .. [255]
empty shard count: 124 first empties: [0, 1, 2, 3, 4, 5]
min count: 0 max count: 3240
```

- 违反说明: `mix` 第 29 行只返回哈希的最低字节 `h & 0xFF`，`key_hash` 的输出因此只有
  256 种取值。10 万个连续键、300 片时，分片 256..299 永远拿不到任何键（另有 0..51 因
  结论 1 的高位偏斜也是空的），共 124 个空桶，最小桶计数为 0、最大桶 3240。
  均匀性被破坏，违反第 1 条保证。

### 结论 3

- 保证编号: 2
- 缺陷位置: shardprng/seed.py:17
- 复现命令: `python3 -c "from shardprng import shard_of; keys=[b'key-%06d'%i for i in range(20000)]; seq=[[shard_of(k,8,s) for k in keys] for s in range(16)]; vals=[sum(1 for i in range(len(keys)) if seq[s][i]==seq[s+1][i])/len(keys) for s in range(15)]; print('expected agreement = %.4f'%0.125); print('adjacent mean = %.4f, min = %.4f, max = %.4f'%(sum(vals)/len(vals),min(vals),max(vals))); print('deviation (mean-expected) = %.1f pct-points'%((sum(vals)/len(vals)-0.125)*100))"`
- 实际输出:

```
expected agreement = 0.1250
adjacent mean = 0.8053, min = 0.8005, max = 0.8109
deviation (mean-expected) = 68.0 pct-points
```

- 违反说明: `derive_seed(seed, index) = seed + index`（第 17 行），基础 `seed` 与 `seed+1`
  的 8 个 lane 种子集合 `{seed..seed+7}` 与 `{seed+1..seed+8}` 有 7/8 重合，取 max 后
  两条序列几乎总是由同一个 lane 决定。固定输入（2 万个连续键、8 片）下相邻 15 对种子的
  同键同片率平均 0.8053，而第 2 条保证要求 ≈ `1/8 = 0.1250`，偏差 68 个百分点，远超 3%。

### 结论 4

- 保证编号: 3
- 缺陷位置: shardprng/rebalance.py:9
- 复现命令: `python3 -c "from shardprng import moved_fraction; keys=[b'key-%06d'%i for i in range(100000)]; print('moved_fraction 7->8  = %.4f (expected ~%.4f)'%(moved_fraction(keys,7,8),1/8)); print('moved_fraction 49->50= %.4f (expected ~%.4f)'%(moved_fraction(keys,49,50),1/50))"`
- 实际输出:

```
moved_fraction 7->8  = 1.0000 (expected ~0.1250)
moved_fraction 49->50= 1.0000 (expected ~0.0200)
```

- 违反说明: `remap` 第 9 行 `(old + (new_shards - old_shards)) % new_shards` 在
  `old_shards = N, new_shards = N+1` 时化简为 `(old + 1) % (N+1)`，对任何旧分片号
  `old`（0..N-1）都不等于原号，因此 `moved_fraction` 恒为 1.0（100% 的键换桶），
  而第 3 条保证要求只有约 `1/(N+1)`（7→8 约 0.125，49→50 约 0.02）。

### 结论 5

- 保证编号: 3
- 缺陷位置: shardprng/bucket.py:8
- 复现命令: `python3 -c "from shardprng import shard_of; keys=[b'key-%06d'%i for i in range(20000)]; n=7; m=sum(1 for k in keys if shard_of(k,n)!=shard_of(k,n+1))/len(keys); print('7->8 actual moved via shard_of = %.4f'%m); print('expected ~%.4f'%(1/8)); print('deviation = %.1f pct-points'%((m-1/8)*100))"`
- 实际输出:

```
7->8 actual moved via shard_of = 0.8912
expected ~0.1250
deviation = 76.6 pct-points
```

- 违反说明: 即使不看 `remap`、直接对同一个键比较 `shard_of(key, 7)` 与 `shard_of(key, 8)`，
  第 8 行的映射是 `value % shards`。取模在分片数 +1 时会重算几乎全部键的归属，
  固定输入下 7→8 实际换桶比例为 0.8912，不是第 3 条保证要求的约 `1/8 = 0.125`，
  偏差 76.6 个百分点；该取模映射不具备一致性哈希性质。

### 结论 6

- 保证编号: 7
- 缺陷位置: shardprng/bucket.py:16
- 复现命令:
  ```
  python3 -c "from shardprng import shard_of
  for n in (0,-1):
      try:
          r=shard_of(b'abc',n); print('shards=%r returned %r (expected ValueError)'%(n,r))
      except ValueError as e:
          print('shards=%r ValueError: %s'%(n,e))
      except Exception as e:
          print('shards=%r raised %s (expected ValueError)'%(n,type(e).__name__))"
  ```
- 实际输出:

```
shards=0 raised ZeroDivisionError (expected ValueError)
shards=-1 returned 0 (expected ValueError)
```

- 违反说明: `shard_of`（第 16 行）把 `shards` 原样传给 `value % shards`，全程没有边界校验。
  固定输入下 `shards=0` 抛的是 `ZeroDivisionError` 而非第 7 条保证要求的 `ValueError`；
  `shards=-1` 不但不抛 `ValueError`，还返回了 `0`（一个落在契约区间 `[0, -1)` 之外的结果）。

### 结论 7

- 保证编号: 7
- 缺陷位置: shardprng/seed.py:26
- 复现命令: `python3 -c "import shardprng.seed as sd; counter=[0]; orig=sd.mix
def counting(key,seed):
    counter[0]+=len(key); return orig(key,seed)
sd.mix=counting
from shardprng import shard_of
counter[0]=0; shard_of(b'a',8); short=counter[0]
counter[0]=0; shard_of(b'a'*(1024*1024),8); long=counter[0]
print('bytes processed 1-byte key =',short); print('bytes processed 1MiB key =',long); print('ratio long/short =',long//short); print('fixed-length digest expected: ratio ~1')"`
- 实际输出:

```
bytes processed 1-byte key = 8
bytes processed 1MiB key = 8388608
ratio long/short = 1048576
fixed-length digest expected: ratio ~1
```

- 违反说明: `mix` 第 26 行 `for byte in value` 对 key 逐字节扫描，`key_hash` 又在 8 条 lane
  上各扫一遍；key 在分片前没有被摘要成定长值。固定输入（仅用包装对象计数，不用时间、不用
  系统随机源）下 1 字节键被读取 8 个字节、1 MiB 键被读取 8,388,608 个字节，处理量与键长
  严格线性（比值 1,048,576），长键必然显著慢于短键，违反第 7 条保证。

### 结论 8

- 保证编号: 4
- 缺陷位置: shardprng/bucket.py:28
- 复现命令: `python3 -c "from shardprng import histogram; keys=[b'key-%03d'%i for i in range(64)]; fwd=histogram(keys,8); rev=histogram(list(reversed(keys)),8); print('forward shard order :',[r['shard'] for r in fwd]); print('reversed shard order:',[r['shard'] for r in rev]); print('same key set, output equal?',fwd==rev)"`
- 实际输出:

```
forward shard order : [2, 1, 3, 4, 6, 5, 0, 7]
reversed shard order: [4, 1, 5, 3, 6, 0, 2, 7]
same key set, output equal? False
```

- 违反说明: `histogram` 第 28 行按 `counts` 字典的插入顺序产出列表，而插入顺序取决于键被
  送入的先后（第 24-27 行）。同样 64 个键的集合，正序与逆序调用得到的逐字段列表不同
  （`False`），库给出的统计结果随调用/分配顺序改变，违反第 4 条保证。

## 既有用例的覆盖范围

`tests/test_shardprng.py` 共 14 个用例，只覆盖：64 个小规模连续键、单线程、少量固定分片数
（2/3/5/8/16 等）下的返回值区间、同参确定性、`seed=0` 与 `seed=7` 结果不相等、计数总和、
`remap` 同分片数、`moved_fraction` 落在 0..1、以及 `mix`/`key_hash` 的返回区间。

未覆盖：10 万键级别的均匀度阈值（第 1 条）、相邻 `seed` 的两两重合率（第 2 条）、
N→N+1 的真实搬动比例与一致性哈希性质（第 3 条）、同一键集不同送入顺序下 `histogram`
输出的稳定性（第 4 条）、跨进程 `PYTHONHASHSEED` 一致性（第 5 条）、`shards=0`/负数等
非法入参的异常类型、以及长键（1 MiB）是否先被摘要成定长（第 7 条）。
