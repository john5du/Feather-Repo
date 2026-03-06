"""格式化工具测试"""

import unittest
from datetime import datetime
from feather.utils.formatters import ReleaseInfoExtractor


class TestReleaseInfoExtractor(unittest.TestCase):
    """ReleaseInfoExtractor 测试"""

    def test_extract_description_simple(self):
        """测试简单描述提取"""
        body = "This is the release notes.\n\nMore details here."
        result = ReleaseInfoExtractor.extract_description(body)

        self.assertIn("This is the release notes", result)

    def test_extract_description_with_html(self):
        """测试HTML标签分割"""
        body = "Release notes here<div class='details'>More info</div>"
        result = ReleaseInfoExtractor.extract_description(body)

        self.assertEqual(result, "Release notes here")

    def test_extract_description_with_separator(self):
        """测试分隔符分割"""
        body = "Notes---\nOther content"
        result = ReleaseInfoExtractor.extract_description(body)

        self.assertEqual(result, "Notes")

    def test_extract_description_empty(self):
        """测试空描述"""
        result = ReleaseInfoExtractor.extract_description("")
        self.assertEqual(result, "")

    def test_extract_version_from_tag(self):
        """测试从tag提取版本"""
        # 移除v前缀
        self.assertEqual(
            ReleaseInfoExtractor.extract_version_from_tag('v1.0.0'),
            '1.0.0'
        )

        # 移除后缀
        self.assertEqual(
            ReleaseInfoExtractor.extract_version_from_tag('v1.0.0-release'),
            '1.0.0'
        )

        # 空tag
        self.assertEqual(
            ReleaseInfoExtractor.extract_version_from_tag(''),
            ''
        )

    def test_format_iso_date(self):
        """测试ISO日期格式"""
        dt = datetime(2026, 3, 6, 10, 30, 45)
        result = ReleaseInfoExtractor.format_iso_date(dt)

        self.assertIn('2026-03-06', result)
        self.assertIn('10:30:45', result)

    def test_format_date_short(self):
        """测试短日期格式"""
        dt = datetime(2026, 3, 6)
        result = ReleaseInfoExtractor.format_date_short(dt)

        self.assertEqual(result, '2026-03-06')


if __name__ == '__main__':
    unittest.main()
