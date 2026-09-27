"""分片选择与分布统计。"""

from . import seed as _seed


def bucket_of(value, shards):
    """把校验值 ``value`` 归一到 ``[0, shards)``。"""
    return value % shards


def shard_of(key, shards, seed=0):
    """把 ``key`` 分到 ``shards`` 个分片之一；``seed`` 用于区分不同批次。

    返回 ``[0, shards)`` 内的整数。
    """
    return bucket_of(_seed.key_hash(key, seed), shards)


def histogram(keys, shards, seed=0):
    """统计每片的键数量。

    返回 ``[{"shard": 分片号, "count": 键数}, ...]``。
    """
    counts = {}
    for key in keys:
        index = shard_of(key, shards, seed)
        counts[index] = counts.get(index, 0) + 1
    return [{"shard": index, "count": count} for index, count in counts.items()]
