#!/usr/bin/env python3
"""灰度环境抓下来的一段最小输入。

10 万个连续键、50 个分片，把每个分片的键数统计出来，并给出
「最大桶 - 最小桶」相对均值（每一片的平均键数）的百分比。
脚本自己按 3% 的阈值判断分布是否可接受，异常时退出码为 1。

跑法::

    python3 repro.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shardprng import histogram  # noqa: E402

KEY_COUNT = 100000
SHARDS = 50
TOLERANCE = 0.03


def main():
    keys = [b"key-%06d" % index for index in range(KEY_COUNT)]
    counts = {index: 0 for index in range(SHARDS)}
    for row in histogram(keys, SHARDS):
        counts[row["shard"]] = row["count"]

    low = min(counts.values())
    high = max(counts.values())
    mean = KEY_COUNT / SHARDS
    spread = (high - low) / mean

    print("分片数     =", SHARDS)
    print("键数       =", KEY_COUNT)
    print("最少的一片 =", low)
    print("最多的一片 =", high)
    print("最大最小差 = %.1f%%（阈值 %.1f%%）" % (spread * 100, TOLERANCE * 100))

    if spread > TOLERANCE:
        print("=> 分布异常")
        return 1
    print("=> 分布正常")
    return 0


if __name__ == "__main__":
    sys.exit(main())
