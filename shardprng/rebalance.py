"""分片数变更时的重映射。"""

from . import bucket as _bucket


def remap(key, old_shards, new_shards, seed=0):
    """分片数由 ``old_shards`` 改成 ``new_shards`` 后，``key`` 的新分片号。"""
    old = _bucket.shard_of(key, old_shards, seed)
    return (old + (new_shards - old_shards)) % new_shards


def moved_fraction(keys, old_shards, new_shards, seed=0):
    """统计分片数变更后「换了分片」的键占比。"""
    total = 0
    moved = 0
    for key in keys:
        total += 1
        if _bucket.shard_of(key, old_shards, seed) != remap(key, old_shards, new_shards, seed):
            moved += 1
    if total == 0:
        return 0.0
    return moved / total
