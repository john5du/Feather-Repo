"""GitHub仓库更新服务"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from fnmatch import fnmatch
from typing import Dict, List, Optional, Sequence, Tuple

from feather.core.config import ConfigManager, RepositoryConfig
from feather.core.json_handler import JSONHandler
from feather.core.logger import FeatherLogger
from feather.models.app import AppInfo, VersionEntry
from feather.services.github_client import GitHubClient
from feather.utils.formatters import ReleaseInfoExtractor
from feather.utils.validators import AppValidator


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
    failed_count: int = 0
    updated_files: List[str] = field(default_factory=list)
    stats: List[UpdateStat] = field(default_factory=list)


class RepositoryUpdater:
    """GitHub仓库更新服务"""

    def __init__(
        self,
        config: ConfigManager,
        logger: FeatherLogger,
        json_handler: JSONHandler = None,
        github_client: GitHubClient = None,
    ):
        self.config = config
        self.logger = logger
        self.json_handler = json_handler or JSONHandler()
        self.paths = config.get_paths()
        self.update_config = config.get_update()

        try:
            self.github_client = github_client or GitHubClient(
                config.get_github_token(),
                max_retries=self.update_config.max_retries,
            )
        except ValueError as e:
            self.logger.error(f"GitHub Token 配置错误: {e}")
            self.github_client = None

    def update_all(self) -> UpdateResult:
        """更新所有仓库（支持并发）"""
        result = UpdateResult()

        if not self.github_client:
            self.logger.error("GitHub 客户端未初始化，无法继续")
            result.success = False
            return result

        try:
            repos = self.config.get_repos()
            if not repos:
                self.logger.error("未配置任何仓库")
                result.success = False
                return result

            self.logger.info(f"准备更新 {len(repos)} 个仓库")
            max_workers = max(1, min(self.update_config.max_workers, len(repos)))

            stats_by_name: Dict[str, UpdateStat] = {}
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(self.update_single_repo, repo_config): repo_config
                    for repo_config in repos
                }
                for future in as_completed(futures):
                    repo_config = futures[future]
                    try:
                        stat = future.result()
                    except Exception as e:
                        stat = UpdateStat(
                            repo_name=repo_config.name,
                            success=False,
                            message=str(e),
                        )
                        self.logger.error(f"  {repo_config.name} 更新异常: {e}")
                    stats_by_name[stat.repo_name] = stat

            # 按配置顺序输出统计
            for repo_config in repos:
                stat = stats_by_name.get(
                    repo_config.name,
                    UpdateStat(repo_name=repo_config.name, success=False, message="未知错误"),
                )
                result.stats.append(stat)
                if stat.updated:
                    result.updated_count += 1
                    result.updated_files.append(repo_config.json_file)
                if not stat.success:
                    result.failed_count += 1

            result.success = result.failed_count == 0
            self._print_statistics(result)
            return result

        except Exception as e:
            self.logger.error("更新过程中发生错误", exception=e)
            result.success = False
            return result

    def update_single_repo(self, repo_config: RepositoryConfig) -> UpdateStat:
        """更新单个仓库"""
        stat = UpdateStat(repo_name=repo_config.name)

        try:
            release_info = self.github_client.extract_release_info(
                repo_config.owner,
                repo_config.repo,
            )

            ipa_asset = self._find_ipa_asset(
                release_info["assets"],
                repo_config.ipa_filename_patterns,
            )

            if not ipa_asset:
                asset_names = [asset.get("name", "") for asset in release_info["assets"]]
                patterns = ", ".join(repo_config.ipa_filename_patterns)
                stat.message = f"未找到匹配 [{patterns}] 的IPA文件"
                self.logger.warning(
                    f"  {stat.message}",
                    {
                        "patterns": patterns,
                        "assets": ", ".join(asset_names) or "none",
                    },
                )
                return stat

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

            apps_list = all_data.get("apps", [])
            if not apps_list:
                stat.message = "apps数组为空"
                self.logger.warning(f"  {stat.message}")
                return stat

            selected = self._select_target_app(apps_list, repo_config)
            if not selected:
                stat.message = "无法唯一定位要更新的应用条目"
                self.logger.warning(f"  {stat.message}")
                return stat

            app_index, app = selected

            new_version = ReleaseInfoExtractor.extract_version_from_tag(
                release_info["tag_name"]
            )
            new_download_url = ipa_asset["url"]

            if app.version == new_version and app.downloadURL == new_download_url:
                stat.success = True
                stat.message = f"已是最新版本 (v{new_version})"
                self.logger.info(f"  {stat.message}")
                return stat

            old_version = app.version
            app.version = new_version
            app.versionDate = ReleaseInfoExtractor.format_iso_date(
                release_info["published_at"]
            )
            app.downloadURL = new_download_url
            app.size = ipa_asset["size"]

            description = ReleaseInfoExtractor.extract_description(
                release_info["body"]
            )
            app.versionDescription = description
            app.changelog = description
            app.mark_fields_present(
                "version",
                "versionDate",
                "downloadURL",
                "size",
                "versionDescription",
                "changelog",
                "versions",
            )

            self._update_versions_array(
                app,
                new_version,
                description,
                new_download_url,
                ipa_asset["size"],
                repo_config.min_os_version,
                release_info["published_at"],
            )

            app_dict = app.to_dict()
            ok, err = AppValidator.validate_app_info(app_dict)
            if not ok:
                stat.message = f"校验失败: {err}"
                self.logger.error(f"  {stat.message}")
                return stat

            all_data["apps"][app_index] = app_dict

            if self.json_handler.save(repo_config.json_file, all_data):
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
    def _find_ipa_asset(
        assets: List[Dict],
        patterns: Optional[Sequence[str]] = None,
    ) -> Optional[Dict]:
        """
        按 pattern 优先级查找 IPA。

        patterns 按顺序匹配，先命中的 pattern 优先；
        同一 pattern 内取资源列表中的第一个匹配项。
        """
        if not patterns:
            patterns = ["*.ipa"]

        for pattern in patterns:
            for asset in assets:
                name = asset.get("name", "")
                if name.endswith(".ipa") and fnmatch(name, pattern):
                    return asset
        return None

    @staticmethod
    def _select_target_app(
        apps_list: List[Dict],
        repo_config: RepositoryConfig,
    ) -> Optional[Tuple[int, AppInfo]]:
        """按确定性规则选择要更新的应用条目"""
        parsed_apps: List[Tuple[int, AppInfo]] = []
        for index, app_data in enumerate(apps_list):
            if not isinstance(app_data, dict):
                continue
            try:
                parsed_apps.append((index, AppInfo.from_dict(app_data)))
            except Exception:
                continue

        if len(parsed_apps) == 1:
            return parsed_apps[0]

        exact_name_matches = [
            item for item in parsed_apps
            if item[1].name == repo_config.name
        ]
        if len(exact_name_matches) == 1:
            return exact_name_matches[0]

        bundle_matches = [
            item for item in parsed_apps
            if item[1].bundleIdentifier
            and repo_config.name.lower() in item[1].bundleIdentifier.lower()
        ]
        if len(bundle_matches) == 1:
            return bundle_matches[0]

        return None

    @staticmethod
    def _update_versions_array(
        app: AppInfo,
        new_version: str,
        description: str,
        download_url: str,
        size: int,
        min_os_version: str,
        published_at,
    ):
        """更新版本数组"""
        if not app.versions:
            app.versions = []

        version_exists = any(v.version == new_version for v in app.versions)

        if not version_exists:
            new_entry = VersionEntry(
                version=new_version,
                date=ReleaseInfoExtractor.format_date_short(published_at),
                downloadURL=download_url,
                size=size,
                minOSVersion=min_os_version,
                localizedDescription=description,
                _field_order=[
                    "version",
                    "date",
                    "downloadURL",
                    "size",
                    "minOSVersion",
                    "localizedDescription",
                ],
            )
            app.versions.insert(0, new_entry)

            if len(app.versions) > 20:
                app.versions = app.versions[:20]

    def _print_statistics(self, result: UpdateResult):
        """打印统计信息"""
        print("\n" + "=" * 80)
        print("更新统计:")
        print(f"  ✓ 已更新: {result.updated_count} 个")
        print(f"  ✗ 失败: {result.failed_count} 个")
        print(f"  处理仓库: {len(result.stats)} 个")
        print(f"  总体成功: {result.success}")

        if result.updated_files:
            print("\n已更新的文件:")
            for file in result.updated_files:
                print(f"  - {file}")

        failed = [s for s in result.stats if not s.success]
        if failed:
            print("\n失败详情:")
            for stat in failed:
                print(f"  - {stat.repo_name}: {stat.message}")

        print("=" * 80)
