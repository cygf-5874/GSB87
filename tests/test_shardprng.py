"""shardprng 的既有用例。

覆盖范围有意保持很小：小规模键集、单线程、连续键。
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shardprng import bucket_of, histogram, moved_fraction, remap, shard_of  # noqa: E402
from shardprng.seed import key_hash, mix  # noqa: E402

KEYS = [b"key-%03d" % index for index in range(64)]


class ShardOfTest(unittest.TestCase):
    def test_range_various_shards(self):
        for shards in (2, 3, 5, 8, 16):
            for key in KEYS:
                self.assertGreaterEqual(shard_of(key, shards), 0)
                self.assertLess(shard_of(key, shards), shards)

    def test_deterministic(self):
        for key in KEYS:
            self.assertEqual(shard_of(key, 8), shard_of(key, 8))

    def test_seed_changes_some_keys(self):
        first = [shard_of(key, 8, 0) for key in KEYS]
        second = [shard_of(key, 8, 7) for key in KEYS]
        self.assertNotEqual(first, second)

    def test_key_types(self):
        self.assertIn(shard_of(b"abc", 5), range(5))
        self.assertIn(shard_of(b"", 5), range(5))
        self.assertIn(shard_of(b"a" * 4096, 5), range(5))

    def test_order_independent(self):
        forward = {key: shard_of(key, 8) for key in KEYS}
        backward = {key: shard_of(key, 8) for key in reversed(KEYS)}
        self.assertEqual(forward, backward)

    def test_bucket_of_range(self):
        for value in (0, 1, 7, 255):
            self.assertIn(bucket_of(value, 8), range(8))


class HistogramTest(unittest.TestCase):

    def test_total(self):
        rows = histogram(KEYS, 8)
        self.assertEqual(sum(row["count"] for row in rows), len(KEYS))

    def test_shards_in_range(self):
        rows = histogram(KEYS, 8)
        self.assertTrue(all(0 <= row["shard"] < 8 for row in rows))

    def test_counts_match_shard_of(self):
        counts = {row["shard"]: row["count"] for row in histogram(KEYS, 8)}
        for shard, count in counts.items():
            expected = sum(1 for key in KEYS if shard_of(key, 8) == shard)
            self.assertEqual(count, expected)


class RebalanceTest(unittest.TestCase):
    def test_remap_range(self):
        for key in KEYS:
            self.assertIn(remap(key, 4, 7), range(7))

    def test_remap_same_shards(self):
        for key in KEYS:
            self.assertEqual(remap(key, 5, 5), shard_of(key, 5))

    def test_moved_fraction_bounds(self):
        fraction = moved_fraction(KEYS, 4, 8)
        self.assertGreaterEqual(fraction, 0.0)
        self.assertLessEqual(fraction, 1.0)


class SeedHelpersTest(unittest.TestCase):
    def test_mix_range(self):
        for key in KEYS:
            self.assertIn(mix(key, 0), range(256))

    def test_key_hash_range(self):
        for key in KEYS:
            self.assertIn(key_hash(key), range(256))


if __name__ == "__main__":
    unittest.main()
