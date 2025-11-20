import unittest
from datetime import datetime, timedelta
from src.utils import parse_douyin_time, is_target_comment

class TestUtils(unittest.TestCase):

    def test_is_target_comment(self):
        keywords = ["价格", "怎么买"]
        self.assertEqual(is_target_comment("这就去买，价格多少？", keywords), "价格")
        self.assertEqual(is_target_comment("在哪里可以怎么买到呢", keywords), "怎么买")
        self.assertIsNone(is_target_comment("这视频真好看", keywords))
        self.assertIsNone(is_target_comment("", keywords))

    def test_parse_douyin_time_minute(self):
        # 模拟 "5分钟前"
        now = datetime.now()
        result = parse_douyin_time("5分钟前")
        expected = now - timedelta(minutes=5)
        # 允许 1 秒误差
        self.assertTrue(abs((result - expected).total_seconds()) < 5)

    def test_parse_douyin_time_hour(self):
        now = datetime.now()
        result = parse_douyin_time("2小时前")
        expected = now - timedelta(hours=2)
        self.assertTrue(abs((result - expected).total_seconds()) < 5)

    def test_parse_douyin_time_yesterday(self):
        now = datetime.now()
        result = parse_douyin_time("昨天")
        expected = now - timedelta(days=1)
        # 昨天通常指昨天的某个时间，这里简化为当前时间减1天，只比较日期可能更准
        self.assertEqual(result.date(), expected.date())

    def test_parse_douyin_time_date(self):
        result = parse_douyin_time("2023-01-01")
        self.assertEqual(result.year, 2023)
        self.assertEqual(result.month, 1)
        self.assertEqual(result.day, 1)

if __name__ == '__main__':
    unittest.main()

