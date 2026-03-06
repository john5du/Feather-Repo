"""验证器测试"""

import unittest
from feather.utils.validators import AppValidator, VersionValidator, URLValidator


class TestAppValidator(unittest.TestCase):
    """AppValidator 测试"""

    def test_validate_valid_app(self):
        """测试有效的应用信息"""
        data = {
            'name': 'TestApp',
            'bundleIdentifier': 'com.test.app',
            'version': '1.0.0',
            'versionDate': '2026-03-06T10:00:00Z',
            'downloadURL': 'https://example.com/app.ipa',
            'size': 1024,
        }

        is_valid, error = AppValidator.validate_app_info(data)
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_validate_missing_fields(self):
        """测试缺少必需字段"""
        data = {
            'name': 'TestApp',
            'bundleIdentifier': 'com.test.app',
            # 缺少其他必需字段
        }

        is_valid, error = AppValidator.validate_app_info(data)
        self.assertFalse(is_valid)
        self.assertIn('缺少', error)

    def test_validate_invalid_type(self):
        """测试无效的字段类型"""
        data = {
            'name': 'TestApp',
            'bundleIdentifier': 'com.test.app',
            'version': '1.0.0',
            'versionDate': '2026-03-06T10:00:00Z',
            'downloadURL': 'https://example.com/app.ipa',
            'size': 'not_an_int',  # 应该是整数
        }

        is_valid, error = AppValidator.validate_app_info(data)
        self.assertFalse(is_valid)

    def test_validate_json_structure(self):
        """测试JSON结构验证"""
        data = {'apps': []}
        is_valid, error = AppValidator.validate_json_structure(data)
        self.assertTrue(is_valid)

        # 缺少apps键
        is_valid, error = AppValidator.validate_json_structure({})
        self.assertFalse(is_valid)


class TestVersionValidator(unittest.TestCase):
    """VersionValidator 测试"""

    def test_validate_version_format(self):
        """测试版本号格式"""
        # 有效的版本号
        is_valid, error = VersionValidator.validate_version_format('1.0.0')
        self.assertTrue(is_valid)

        # 无效的版本号
        is_valid, error = VersionValidator.validate_version_format('1')
        self.assertFalse(is_valid)

        # 空版本号
        is_valid, error = VersionValidator.validate_version_format('')
        self.assertFalse(is_valid)

    def test_validate_version_array(self):
        """测试版本数组"""
        valid_versions = [
            {
                'version': '1.0.0',
                'date': '2026-03-06',
                'downloadURL': 'https://example.com/app.ipa',
                'size': 1024,
            }
        ]

        is_valid, error = VersionValidator.validate_version_array(valid_versions)
        self.assertTrue(is_valid)

        # 超过限制（20个）
        long_versions = [
            {
                'version': f'1.0.{i}',
                'date': '2026-03-06',
                'downloadURL': 'https://example.com/app.ipa',
                'size': 1024,
            }
            for i in range(21)
        ]

        is_valid, error = VersionValidator.validate_version_array(long_versions)
        self.assertFalse(is_valid)


class TestURLValidator(unittest.TestCase):
    """URLValidator 测试"""

    def test_validate_url(self):
        """测试URL验证"""
        # 有效的URL
        is_valid, _ = URLValidator.validate_download_url('https://example.com/app.ipa')
        self.assertTrue(is_valid)

        # HTTP URL
        is_valid, _ = URLValidator.validate_download_url('http://example.com/app.ipa')
        self.assertTrue(is_valid)

        # 无效的URL
        is_valid, _ = URLValidator.validate_download_url('not_a_url')
        self.assertFalse(is_valid)

        # 空URL
        is_valid, _ = URLValidator.validate_download_url('')
        self.assertFalse(is_valid)


if __name__ == '__main__':
    unittest.main()
