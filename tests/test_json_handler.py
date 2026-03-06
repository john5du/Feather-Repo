"""JSON处理器测试"""

import unittest
import json
import tempfile
from pathlib import Path

from feather.core.json_handler import JSONHandler


class TestJSONHandler(unittest.TestCase):
    """JSONHandler 测试"""

    def setUp(self):
        """测试前准备"""
        self.handler = JSONHandler()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        """测试后清理"""
        self.temp_dir.cleanup()

    def test_save_and_load(self):
        """测试保存和加载"""
        test_data = {
            'apps': [
                {
                    'name': 'TestApp',
                    'bundleIdentifier': 'com.test.app',
                    'version': '1.0.0'
                }
            ]
        }

        filepath = self.temp_path / 'test.json'

        # 保存
        result = self.handler.save(str(filepath), test_data, backup=False)
        self.assertTrue(result)
        self.assertTrue(filepath.exists())

        # 加载
        loaded = self.handler.load(str(filepath))
        self.assertEqual(loaded, test_data)

    def test_load_nonexistent_file(self):
        """测试加载不存在的文件"""
        with self.assertRaises(FileNotFoundError):
            self.handler.load(str(self.temp_path / 'nonexistent.json'))

    def test_backup_creation(self):
        """测试备份创建"""
        filepath = self.temp_path / 'test.json'
        test_data = {'test': 'data'}

        # 首次保存
        self.handler.save(str(filepath), test_data, backup=False)

        # 第二次保存（应该创建备份）
        test_data['test'] = 'updated'
        self.handler.save(str(filepath), test_data, backup=True)

        # 检查备份目录
        backup_dir = filepath.parent / '.backups'
        self.assertTrue(backup_dir.exists())
        self.assertTrue(len(list(backup_dir.glob('test_*'))) > 0)

    def test_validate_structure(self):
        """测试结构验证"""
        valid_data = {'apps': []}
        is_valid, error = self.handler.validate_structure(valid_data, ['apps'])
        self.assertTrue(is_valid)
        self.assertIsNone(error)

        # 测试缺少必需键
        invalid_data = {}
        is_valid, error = self.handler.validate_structure(invalid_data, ['apps'])
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)

    def test_get_app_list(self):
        """测试获取应用列表"""
        data = {
            'apps': [
                {'name': 'App1'},
                {'name': 'App2'},
            ]
        }

        apps = self.handler.get_app_list(data)
        self.assertEqual(len(apps), 2)

        # 测试apps不是列表
        data['apps'] = 'not_a_list'
        apps = self.handler.get_app_list(data)
        self.assertEqual(apps, [])


if __name__ == '__main__':
    unittest.main()
