"""GitHub仓库更新服务"""

from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import timezone, datetime

from feather.core.json_handler import JSONHandler
from feather.core.logger import FeatherLogger
from feather.core.config import ConfigManager, RepositoryConfig
from feather.models.app import AppInfo, VersionEntry
from feather.services.github_client import GitHubClient
from feather.utils.formatters import ReleaseInfoExtractor


@dataclass
class UpdateStat:
    """单个仓库更新统计"""
    repo_name: str
    success: bool = False
    updated: bool = False
    message: str = ""


@dataclass
class UpdateResult:
    """更新结果统计"""
    success: bool = True
    updated_count: int = 0
    updated_files: List[str] = None
    stats: List[UpdateStat] = None

    def __post_init__(self):
        if self.updated_files is None:
            self.updated_files = []
        if self.stats is None:
            self.stats = []


class RepositoryUpdater:
    """GitHub仓库更新服务"""

    def __init__(
        self,
        config: ConfigManager,
        logger: FeatherLogger,
        json_handler: JSONHandler = None,
        github_client: GitHubClient = None
    ):
        """
        初始化RepositoryUpdater

        Args:
            config: 配置管理器
            logger: 日志记录器
            json_handler: JSON处理器（可选）
            github_client: GitHub客户端（可选）
        """
        self.config = config
        self.logger = logger
        self.json_handler = json_handler or JSONHandler()
        self.paths = config.get_paths()

        try:
            self.github_client = github_client or GitHubClient(
                config.get_github_token()
            )
        except ValueError as e:
            self.logger.error(f"GitHub Token 配置错误: {e}")
            self.github_client = None

    def update_all(self) -> UpdateResult:
        """
        更新所有仓库

        Returns:
            UpdateResult 更新结果
        """
        result = UpdateResult()

        if not self.github_client:
            self.logger.error("GitHub 客户端未初始化，无法继续")
            result.success = False
            return result

        try:
            repos = self.config.get_repos()
            self.logger.info(f"准备更新 {len(repos)} 个仓库")

            for repo_config in repos:
                self.logger.info(f"更新 {repo_config.name}...")
                stat = self.update_single_repo(repo_config)
                result.stats.append(stat)

                if stat.updated:
                    result.updated_count += 1
                    result.updated_files.append(repo_config.json_file)

            self._print_statistics(result)
            return result

        except Exception as e:
            self.logger.error("更新过程中发生错误", exception=e)
            result.success = False
            return result

    def update_single_repo(self, repo_config: RepositoryConfig) -> UpdateStat:
        """
        更新单个仓库

        Args:
            repo_config: 仓库配置

        Returns:
            UpdateStat 更新统计
        """
        stat = UpdateStat(repo_name=repo_config.name)

        try:
            # 获取最新Release
            release_info = self.github_client.extract_release_info(
                repo_config.owner,
                repo_config.repo
            )

            # 查找IPA文件
            ipa_asset = self._find_ipa_asset(release_info['assets'])

            if not ipa_asset:
                stat.message = f"未找到IPA文件"
                self.logger.warning(f"  {stat.message}")
                return stat

            # 读取现有JSON文件
            try:
                all_data = self.json_handler.load(repo_config.json_file)
            except FileNotFoundError:
                self.logger.error(f"  文件不存在: {repo_config.json_file}")
                stat.message = "文件不存在"
                return stat
            except Exception as e:
                self.logger.error(f"  读取文件失败: {e}")
                stat.message = "读取文件失败"
                return stat

            # 提取应用数据
            apps_list = all_data.get('apps', [])
            if not apps_list:
                stat.message = "apps数组为空"
                self.logger.warning(f"  {stat.message}")
                return stat

            app_data = apps_list[0]

            # 解析应用信息
            try:
                app = AppInfo.from_dict(app_data)
            except Exception as e:
                self.logger.error(f"  解析应用数据失败: {e}")
                stat.message = "解析应用数据失败"
                return stat

            # 比较版本
            new_version = ReleaseInfoExtractor.extract_version_from_tag(
                release_info['tag_name']
            )
            new_download_url = ipa_asset['url']

            if (app.version == new_version and
                app.downloadURL == new_download_url):
                stat.message = f"已是最新版本 (v{new_version})"
                self.logger.info(f"  {stat.message}")
                return stat

            # 更新应用信息
            old_version = app.version
            app.version = new_version
            app.versionDate = ReleaseInfoExtractor.format_iso_date(
                release_info['published_at']
            )
            app.downloadURL = new_download_url
            app.size = ipa_asset['size']

            # 提取版本描述
            description = ReleaseInfoExtractor.extract_description(
                release_info['body']
            )
            app.versionDescription = description
            app.changelog = description

            # 更新versions数组
            self._update_versions_array(
                app,
                new_version,
                description,
                new_download_url,
                ipa_asset['size'],
                repo_config.min_os_version
            )

            # 保存JSON文件
            all_data['apps'][0] = app.to_dict()

            if self.json_handler.save(
                repo_config.json_file,
                all_data,
            ):
                stat.success = True
                stat.updated = True
                stat.message = f"已从 v{old_version} 更新到 v{new_version}"
                self.logger.info(f"  ✓ {stat.message}")
            else:
                stat.message = "保存文件失败"

            return stat

        except Exception as e:
            stat.message = str(e)
            self.logger.error(f"  更新失败: {e}")
            return stat

    @staticmethod
    def _find_ipa_asset(assets: List[Dict]) -> Optional[Dict]:
        """
        从资源列表中查找IPA文件

        Args:
            assets: 资源列表

        Returns:
            IPA资源字典或None
        """
        for asset in assets:
            if asset['name'].endswith('.ipa'):
                return asset

        return None

    @staticmethod
    def _update_versions_array(
        app: AppInfo,
        new_version: str,
        description: str,
        download_url: str,
        size: int,
        min_os_version: str
    ):
        """
        更新版本数组

        Args:
            app: 应用对象
            new_version: 新版本号
            description: 版本描述
            download_url: 下载URL
            size: 文件大小
            min_os_version: 最低OS版本
        """
        # 初始化versions数组
        if not app.versions:
            app.versions = []

        # 检查版本是否已存在
        version_exists = any(v.version == new_version for v in app.versions)

        if not version_exists:
            # 创建新版本条目
            new_entry = VersionEntry(
                version=new_version,
                date=datetime.now().strftime("%Y-%m-%d"),
                downloadURL=download_url,
                size=size,
                minOSVersion=min_os_version,
                localizedDescription=description,
            )

            # 添加到前面
            app.versions.insert(0, new_entry)

            # 保持最多20个版本
            if len(app.versions) > 20:
                app.versions = app.versions[:20]

    def _print_statistics(self, result: UpdateResult):
        """打印统计信息"""
        print("\n" + "=" * 80)
        print("更新统计:")
        print(f"  ✓ 已更新: {result.updated_count} 个")
        print(f"  处理仓库: {len(result.stats)} 个")

        if result.updated_files:
            print(f"\n已更新的文件:")
            for file in result.updated_files:
                print(f"  - {file}")

        print("=" * 80)
