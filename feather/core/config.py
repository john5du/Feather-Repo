"""配置管理系统"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import yaml


@dataclass
class PathConfig:
    """路径配置"""
    app_dir: str = "app"
    all_json: str = "all.json"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'app_dir': self.app_dir,
            'all_json': self.all_json,
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
            ),
            logging=LoggingConfig(
                level="INFO",
                format="text",
            ),
        )
        return ConfigManager(config)

    @staticmethod
    def create_from_yaml(config_file: str = "config/repos.yml") -> "ConfigManager":
        """从 YAML 配置文件创建配置"""
        config_path = Path(config_file)
        if not config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_file}")

        with config_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        repositories: List[RepositoryConfig] = []
        for repo in data.get("repositories", []):
            repositories.append(
                RepositoryConfig(
                    name=repo.get("name", ""),
                    owner=repo.get("owner", ""),
                    repo=repo.get("repo", ""),
                    json_file=repo.get("json_file", ""),
                    ipa_filename_pattern=repo.get("ipa_filename_pattern", "*.ipa"),
                    min_os_version=repo.get("min_os_version", "13.0"),
                )
            )

        paths_data = data.get("paths", {})
        logging_data = data.get("logging", {})

        config = Config(
            repositories=repositories,
            paths=PathConfig(
                app_dir=paths_data.get("app_dir", "app"),
                all_json=paths_data.get("all_json", "all.json"),
            ),
            logging=LoggingConfig(
                level=logging_data.get("level", "INFO"),
                format=logging_data.get("format", "text"),
            ),
        )
        return ConfigManager(config)

    @staticmethod
    def create(config_file: str = "config/repos.yml") -> "ConfigManager":
        """从 YAML 配置文件创建配置，失败时显式报错"""
        try:
            return ConfigManager.create_from_yaml(config_file)
        except Exception as e:
            raise RuntimeError(
                f"加载配置文件失败: {config_file}. {e}"
            ) from e

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
