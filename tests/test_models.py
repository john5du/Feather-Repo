"""数据模型测试"""

import unittest
from feather.models.app import AppInfo, VersionEntry


class TestVersionEntry(unittest.TestCase):
    """VersionEntry 测试"""

    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            'version': '1.0.0',
            'date': '2026-03-06',
            'downloadURL': 'https://example.com/app.ipa',
            'size': 1024,
            'minOSVersion': '14.0',
        }

        entry = VersionEntry.from_dict(data)
        self.assertEqual(entry.version, '1.0.0')
        self.assertEqual(entry.date, '2026-03-06')
        self.assertEqual(entry.size, 1024)

    def test_to_dict(self):
        """测试转换为字典"""
        entry = VersionEntry(
            version='1.0.0',
            date='2026-03-06',
            downloadURL='https://example.com/app.ipa',
            size=1024,
        )

        data = entry.to_dict()
        self.assertEqual(data['version'], '1.0.0')
        self.assertIn('downloadURL', data)


class TestAppInfo(unittest.TestCase):
    """AppInfo 测试"""

    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            'name': 'TestApp',
            'bundleIdentifier': 'com.test.app',
            'version': '1.0.0',
            'versionDate': '2026-03-06T10:00:00Z',
            'downloadURL': 'https://example.com/app.ipa',
            'size': 1024,
            'versions': [
                {
                    'version': '1.0.0',
                    'date': '2026-03-06',
                    'downloadURL': 'https://example.com/app.ipa',
                    'size': 1024,
                }
            ],
        }

        app = AppInfo.from_dict(data)
        self.assertEqual(app.name, 'TestApp')
        self.assertEqual(app.bundleIdentifier, 'com.test.app')
        self.assertEqual(len(app.versions), 1)

    def test_get_key(self):
        """测试获取应用标识"""
        app = AppInfo(
            name='TestApp',
            bundleIdentifier='com.test.app',
            version='1.0.0',
            versionDate='2026-03-06T10:00:00Z',
            downloadURL='https://example.com/app.ipa',
            size=1024,
        )

        # 优先使用name
        self.assertEqual(app.get_key(), 'TestApp')

    def test_has_same_version_info(self):
        """测试版本信息比较"""
        app1 = AppInfo(
            name='App1',
            bundleIdentifier='com.app1',
            version='1.0.0',
            versionDate='2026-03-06T10:00:00Z',
            downloadURL='https://example.com/app.ipa',
            size=1024,
        )

        app2 = AppInfo(
            name='App1',
            bundleIdentifier='com.app1',
            version='1.0.0',
            versionDate='2026-03-06T10:00:00Z',
            downloadURL='https://example.com/app.ipa',
            size=1024,
        )

        self.assertTrue(app1.has_same_version_info(app2))

        # 修改版本号
        app2.version = '1.1.0'
        self.assertFalse(app1.has_same_version_info(app2))

    def test_to_dict(self):
        """测试转换为字典"""
        app = AppInfo(
            name='TestApp',
            bundleIdentifier='com.test.app',
            version='1.0.0',
            versionDate='2026-03-06T10:00:00Z',
            downloadURL='https://example.com/app.ipa',
            size=1024,
        )

        data = app.to_dict()
        self.assertEqual(data['name'], 'TestApp')
        self.assertIn('version', data)


if __name__ == '__main__':
    unittest.main()
