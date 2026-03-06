"""配置管理测试"""

import unittest
from feather.core.config import ConfigManager, Config, RepositoryConfig, PathConfig


class TestRepositoryConfig(unittest.TestCase):
    """RepositoryConfig 测试"""

    def test_create_repo_config(self):
        """测试创建仓库配置"""
        repo = RepositoryConfig(
            name="TestRepo",
            owner="test_owner",
            repo="test_repo",
            json_file="app/test.json",
        )

        self.assertEqual(repo.name, "TestRepo")
        self.assertEqual(repo.owner, "test_owner")
        self.assertEqual(repo.min_os_version, "13.0")  # 默认值

    def test_repo_to_dict(self):
        """测试仓库配置转字典"""
        repo = RepositoryConfig(
            name="TestRepo",
            owner="test_owner",
            repo="test_repo",
            json_file="app/test.json",
        )

        data = repo.to_dict()
        self.assertIn('name', data)
        self.assertIn('owner', data)


class TestPathConfig(unittest.TestCase):
    """PathConfig 测试"""

    def test_create_path_config(self):
        """测试创建路径配置"""
        paths = PathConfig(
            app_dir="app",
            all_json="all.json",
        )

        self.assertEqual(paths.app_dir, "app")
        self.assertEqual(paths.all_json, "all.json")
        self.assertFalse(paths.backups_enabled)


class TestConfigManager(unittest.TestCase):
    """ConfigManager 测试"""

    def test_create_default_config(self):
        """测试创建默认配置"""
        manager = ConfigManager.create_default()

        repos = manager.get_repos()
        self.assertEqual(len(repos), 6)  # 6个应用

        # 检查特定应用
        kazumi = [r for r in repos if r.name == 'Kazumi']
        self.assertEqual(len(kazumi), 1)
        self.assertEqual(kazumi[0].owner, 'Predidit')

    def test_get_paths(self):
        """测试获取路径配置"""
        manager = ConfigManager.create_default()
        paths = manager.get_paths()

        self.assertEqual(paths.app_dir, "app")
        self.assertEqual(paths.all_json, "all.json")
        self.assertFalse(paths.backups_enabled)

    def test_get_logging(self):
        """测试获取日志配置"""
        manager = ConfigManager.create_default()
        logging = manager.get_logging()

        self.assertEqual(logging.level, "INFO")

    def test_to_dict(self):
        """测试配置转字典"""
        manager = ConfigManager.create_default()
        data = manager.to_dict()

        self.assertIn('repositories', data)
        self.assertIn('paths', data)
        self.assertIn('logging', data)
        self.assertIn('backups_enabled', data['paths'])
        self.assertFalse(data['paths']['backups_enabled'])


if __name__ == '__main__':
    unittest.main()
