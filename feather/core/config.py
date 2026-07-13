"""配置管理系统"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import yaml


@dataclass
class PathConfig:
    """路径配置"""
    app_dir: str = "app"
    all_json: str = "all.json"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "app_dir": self.app_dir,
            "all_json": self.all_json,
        }


@dataclass
class RepositoryConfig:
    """GitHub仓库配置"""
    name: str
    owner: str
    repo: str
    json_file: str
    ipa_filename_patterns: List[str] = field(default_factory=lambda: ["*.ipa"])
    min_os_version: str = "13.0"

    @property
    def ipa_filename_pattern(self) -> str:
        """兼容旧接口：返回第一个 pattern"""
        return self.ipa_filename_patterns[0] if self.ipa_filename_patterns else "*.ipa"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "owner": self.owner,
            "repo": self.repo,
            "json_file": self.json_file,
            "ipa_filename_pattern": (
                self.ipa_filename_patterns[0]
                if len(self.ipa_filename_patterns) == 1
                else list(self.ipa_filename_patterns)
            ),
            "min_os_version": self.min_os_version,
        }


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"
    format: str = "text"

    def to_dict(self) -> Dict[str, str]:
        return {
            "level": self.level,
            "format": self.format,
        }


@dataclass
class MergeConfig:
    """合并配置"""
    remove_orphans: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {"remove_orphans": self.remove_orphans}


@dataclass
class UpdateConfig:
    """更新配置"""
    max_workers: int = 4
    max_retries: int = 3

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_workers": self.max_workers,
            "max_retries": self.max_retries,
        }


@dataclass
class Config:
    """主配置类"""
    repositories: List[RepositoryConfig] = field(default_factory=list)
    paths: PathConfig = field(default_factory=PathConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    merge: MergeConfig = field(default_factory=MergeConfig)
    update: UpdateConfig = field(default_factory=UpdateConfig)
    github_token: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "repositories": [r.to_dict() for r in self.repositories],
            "paths": self.paths.to_dict(),
            "logging": self.logging.to_dict(),
            "merge": self.merge.to_dict(),
            "update": self.update.to_dict(),
        }


def _parse_ipa_patterns(value: Any) -> List[str]:
    """解析 ipa_filename_pattern（字符串或列表）"""
    if value is None:
        return ["*.ipa"]
    if isinstance(value, str):
        return [value] if value else ["*.ipa"]
    if isinstance(value, list):
        patterns = [str(item) for item in value if item]
        return patterns or ["*.ipa"]
    return ["*.ipa"]


def _repo_from_dict(repo: Dict[str, Any]) -> RepositoryConfig:
    pattern = repo.get("ipa_filename_patterns", repo.get("ipa_filename_pattern", "*.ipa"))
    return RepositoryConfig(
        name=repo.get("name", ""),
        owner=repo.get("owner", ""),
        repo=repo.get("repo", ""),
        json_file=repo.get("json_file", ""),
        ipa_filename_patterns=_parse_ipa_patterns(pattern),
        min_os_version=str(repo.get("min_os_version", "13.0")),
    )


class ConfigManager:
    """配置管理器"""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self._load_env_variables()

    def _load_env_variables(self):
        """从环境变量加载配置"""
        self.config.github_token = os.environ.get(
            "GITHUB_TOKEN",
            self.config.github_token,
        )

    def get_repos(self) -> List[RepositoryConfig]:
        return self.config.repositories

    def get_paths(self) -> PathConfig:
        return self.config.paths

    def get_logging(self) -> LoggingConfig:
        return self.config.logging

    def get_merge(self) -> MergeConfig:
        return self.config.merge

    def get_update(self) -> UpdateConfig:
        return self.config.update

    def get_github_token(self) -> Optional[str]:
        return self.config.github_token

    @staticmethod
    def create_default() -> "ConfigManager":
        """创建与 config/repos.yml 同步的默认配置"""
        return ConfigManager.create_from_yaml("config/repos.yml")

    @staticmethod
    def create_from_yaml(config_file: str = "config/repos.yml") -> "ConfigManager":
        """从 YAML 配置文件创建配置"""
        config_path = Path(config_file)
        if not config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_file}")

        with config_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        repositories = [_repo_from_dict(repo) for repo in data.get("repositories", [])]

        paths_data = data.get("paths", {})
        logging_data = data.get("logging", {})
        merge_data = data.get("merge", {})
        update_data = data.get("update", {})

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
            merge=MergeConfig(
                remove_orphans=bool(merge_data.get("remove_orphans", True)),
            ),
            update=UpdateConfig(
                max_workers=int(update_data.get("max_workers", 4)),
                max_retries=int(update_data.get("max_retries", 3)),
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
        print(f"删除孤儿应用: {self.config.merge.remove_orphans}")
        print(f"更新并发数: {self.config.update.max_workers}")
