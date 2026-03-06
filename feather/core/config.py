"""配置管理系统"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class PathConfig:
    """路径配置"""
    app_dir: str = "app"
    all_json: str = "all.json"
    backups_dir: str = ".backups"
    backups_enabled: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'app_dir': self.app_dir,
            'all_json': self.all_json,
            'backups_dir': self.backups_dir,
            'backups_enabled': self.backups_enabled,
        }


@dataclass
class RepositoryConfig:
    """GitHub仓库配置"""
    name: str
    owner: str
    repo: str
    json_file: str
    ipa_filename_pattern: str = "*.ipa"
    min_os_version: str = "13.0"

    def to_dict(self) -> Dict[str, str]:
        return {
            'name': self.name,
            'owner': self.owner,
            'repo': self.repo,
            'json_file': self.json_file,
            'ipa_filename_pattern': self.ipa_filename_pattern,
            'min_os_version': self.min_os_version,
        }


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"
    format: str = "text"

    def to_dict(self) -> Dict[str, str]:
        return {
            'level': self.level,
            'format': self.format,
        }


@dataclass
class Config:
    """主配置类"""
    repositories: List[RepositoryConfig] = field(default_factory=list)
    paths: PathConfig = field(default_factory=PathConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    github_token: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'repositories': [r.to_dict() for r in self.repositories],
            'paths': self.paths.to_dict(),
            'logging': self.logging.to_dict(),
        }


class ConfigManager:
    """配置管理器"""

    def __init__(self, config: Optional[Config] = None):
        """
        初始化配置管理器

        Args:
            config: Config对象，如果为None则使用默认配置
        """
        self.config = config or Config()
        self._load_env_variables()

    def _load_env_variables(self):
        """从环境变量加载配置"""
        # GitHub Token（从环境变量加载）
        self.config.github_token = os.environ.get(
            'GITHUB_TOKEN',
            self.config.github_token
        )

    def get_repos(self) -> List[RepositoryConfig]:
        """获取所有仓库配置"""
        return self.config.repositories

    def get_paths(self) -> PathConfig:
        """获取路径配置"""
        return self.config.paths

    def get_logging(self) -> LoggingConfig:
        """获取日志配置"""
        return self.config.logging

    def get_github_token(self) -> Optional[str]:
        """获取GitHub Token"""
        return self.config.github_token

    @staticmethod
    def create_default() -> "ConfigManager":
        """
        创建默认配置

        Returns:
            ConfigManager实例
        """
        config = Config(
            repositories=[
                RepositoryConfig(
                    name="Kazumi",
                    owner="Predidit",
                    repo="Kazumi",
                    json_file="app/kazumi.json",
                ),
                RepositoryConfig(
                    name="PiliPlus",
                    owner="bggRGjQaUbCoE",
                    repo="PiliPlus",
                    json_file="app/piliplus.json",
                ),
                RepositoryConfig(
                    name="Fluxdo",
                    owner="Lingyan000",
                    repo="fluxdo",
                    json_file="app/fluxdo.json",
                ),
                RepositoryConfig(
                    name="Harbour",
                    owner="rrroyal",
                    repo="Harbour",
                    json_file="app/harbour.json",
                ),
                RepositoryConfig(
                    name="PeekPili",
                    owner="ingriddaleusag-dotcom",
                    repo="PeekPiliRelease",
                    json_file="app/peekpili.json",
                ),
                RepositoryConfig(
                    name="Asspp",
                    owner="Lakr233",
                    repo="Asspp",
                    json_file="app/asspp.json",
                ),
            ],
            paths=PathConfig(
                app_dir="app",
                all_json="all.json",
                backups_dir=".backups",
                backups_enabled=False,
            ),
            logging=LoggingConfig(
                level="INFO",
                format="text",
            ),
        )
        return ConfigManager(config)

    def to_dict(self) -> Dict[str, Any]:
        """将配置转换为字典"""
        return self.config.to_dict()

    def print_summary(self):
        """打印配置摘要"""
        print("\n=== 配置信息 ===")
        print(f"仓库数量: {len(self.config.repositories)}")
        for repo in self.config.repositories:
            print(f"  - {repo.name} ({repo.owner}/{repo.repo})")
        print(f"日志级别: {self.config.logging.level}")
        print(f"应用目录: {self.config.paths.app_dir}")
        print(f"合并文件: {self.config.paths.all_json}")
        print(f"备份开关: {'开启' if self.config.paths.backups_enabled else '关闭'}")
