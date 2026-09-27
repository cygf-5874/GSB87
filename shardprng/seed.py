"""种子派生与字节混合。

本模块只负责把「基础 seed」与「字节串」折算成一个校验值，供分片选择使用。
所有函数都是纯函数：不读写全局状态，不依赖时间或系统随机源。
"""

MASK = 0xFFFFFFFF
FNV_OFFSET = 0x811C9DC5
FNV_PRIME = 0x01000193

# 折算一个 key 时使用的子种子个数。
LANES = 8


def derive_seed(seed, index):
    """由基础 ``seed`` 与序号 ``index`` 派生第 ``index`` 个子种子。"""
    return (seed + index) & MASK


def mix(value, seed):
    """把字节串 ``value`` 与种子 ``seed`` 混合成一个 0..255 的校验值。

    ``value`` 可以是 ``bytes``（也可以是任何可迭代出 0..255 整数的对象）。
    """
    h = (FNV_OFFSET ^ (seed & MASK)) & MASK
    for byte in value:
        h ^= byte
        h = (h * FNV_PRIME) & MASK
    return h & 0xFF


def key_hash(key, seed=0):
    """把 ``key`` 折算成一个校验值。

    对 ``key`` 分别用 ``seed`` 派生的 ``LANES`` 个子种子混合，
    取其中最大的那个作为结果。
    """
    best = 0
    for index in range(LANES):
        score = mix(key, derive_seed(seed, index))
        if score > best:
            best = score
    return best
