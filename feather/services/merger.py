"""应用合并服务"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Tuple

from feather.core.config import ConfigManager
from feather.core.json_handler import JSONHandler
from feather.core.logger import FeatherLogger
from feather.models.app import AppInfo
from feather.utils.validators import AppValidator


@dataclass
class MergeStat:
    """单个文件合并统计"""
    file: str
    added: int = 0
    updated: int = 0
    unchanged: int = 0

    @property
    def total(self) -> int:
        return self.added + self.updated + self.unchanged


@dataclass
class MergeResult:
    """合并结果统计"""
    success: bool = True
    total_apps: int = 0
    added_count: int = 0
    updated_count: int = 0
    unchanged_count: int = 0
    removed_count: int = 0
    stats: List[MergeStat] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "total_apps": self.total_apps,
            "added": self.added_count,
            "updated": self.updated_count,
            "unchanged": self.unchanged_count,
            "removed": self.removed_count,
        }


class AppMerger:
    """应用合并服务（app/*.json 为 source-of-truth）"""

    def __init__(
        self,
        config: ConfigManager,
        logger: FeatherLogger,
        json_handler: JSONHandler = None,
    ):
        self.config = config
        self.logger = logger
        self.json_handler = json_handler or JSONHandler()
        self.paths = config.get_paths()
        self.merge_config = config.get_merge()

    def merge_all(self) -> MergeResult:
        """执行合并所有应用"""
        result = MergeResult()

        try:
            source_files = self._scan_source_files()

            if not source_files:
                self.logger.warning("未找到任何JSON文件")
                result.success = False
                return result

            self.logger.info(f"发现 {len(source_files)} 个源文件")
            for sf in source_files:
                self.logger.info(f"  - {sf}")

            all_app_list, metadata = self._load_all_json()
            all_apps: Dict[str, AppInfo] = {
                app.get_key(): app
                for app in all_app_list
                if app.get_key()
            }

            self.logger.info(f"all.json 中已有 {len(all_apps)} 个应用")

            source_keys: Set[str] = set()
            for source_file in source_files:
                self._merge_single_file(source_file, all_apps, source_keys, result)

            if self.merge_config.remove_orphans:
                self._remove_orphans(all_apps, source_keys, result)

            self._save_all_json(all_apps, metadata, result)
            self._print_statistics(result)
            return result

        except Exception as e:
            self.logger.error("合并过程中发生错误", exception=e)
            result.success = False
            return result

    def _scan_source_files(self) -> List[str]:
        """扫描源文件"""
        app_dir = Path(self.paths.app_dir)
        source_files = []

        if not app_dir.exists():
            self.logger.warning(f"应用目录不存在: {app_dir}")
            return source_files

        for json_file in sorted(app_dir.glob("*.json")):
            if json_file.name != "all.json":
                source_files.append(str(json_file))

        return source_files

    def _load_all_json(self) -> Tuple[List[AppInfo], Dict]:
        """加载all.json文件"""
        try:
            data = self.json_handler.load(self.paths.all_json)
            metadata = {k: v for k, v in data.items() if k != "apps"}
            apps_data = data.get("apps", [])

            apps = []
            for app_data in apps_data:
                try:
                    apps.append(AppInfo.from_dict(app_data))
                except Exception as e:
                    self.logger.warning(
                        f"解析应用数据失败: {e}",
                        {"app_name": app_data.get("name", "unknown")},
                    )

            return apps, metadata

        except FileNotFoundError:
            self.logger.warning(f"文件不存在: {self.paths.all_json}")
            return [], {}
        except Exception as e:
            self.logger.error("加载all.json失败", exception=e)
            return [], {}

    def _merge_single_file(
        self,
        source_file: str,
        all_apps: Dict[str, AppInfo],
        source_keys: Set[str],
        result: MergeResult,
    ):
        """合并单个源文件"""
        stat = MergeStat(file=source_file)

        try:
            source_data = self.json_handler.load(source_file)
            ok, err = AppValidator.validate_json_structure(source_data)
            if not ok:
                self.logger.warning(f"{source_file} 结构无效: {err}")
                result.stats.append(stat)
                return

            source_apps = source_data.get("apps", [])
            self.logger.info(f"处理 {source_file} ({len(source_apps)} 个应用)")

            for app_data in source_apps:
                if not isinstance(app_data, dict):
                    self.logger.warning("  应用数据格式错误，跳过")
                    continue

                try:
                    ok, err = AppValidator.validate_app_info(app_data)
                    if not ok:
                        self.logger.warning(f"  校验失败，跳过: {err}")
                        continue

                    app = AppInfo.from_dict(app_data)
                    app_key = app.get_key()

                    if not app_key:
                        self.logger.warning("  无法获取应用标识，跳过")
                        continue

                    source_keys.add(app_key)

                    if app_key in all_apps:
                        diff = self._compare_apps(all_apps[app_key], app)
                        if diff:
                            self.logger.info(
                                f"  ✓ 更新应用 '{app_key}'",
                                {"changes": len(diff)},
                            )
                            all_apps[app_key] = app
                            stat.updated += 1
                            result.updated_count += 1
                        else:
                            self.logger.debug(
                                f"  - 应用 '{app_key}' 信息相同，无需更新"
                            )
                            stat.unchanged += 1
                            result.unchanged_count += 1
                    else:
                        self.logger.info(
                            f"  ✓ 添加新应用 '{app_key}' (v{app.version})"
                        )
                        all_apps[app_key] = app
                        stat.added += 1
                        result.added_count += 1

                except Exception as e:
                    self.logger.warning(f"  处理应用失败: {e}")

        except FileNotFoundError:
            self.logger.error(f"源文件不存在: {source_file}")
        except Exception as e:
            self.logger.error(f"处理 {source_file} 时出错", exception=e)

        result.stats.append(stat)

    def _remove_orphans(
        self,
        all_apps: Dict[str, AppInfo],
        source_keys: Set[str],
        result: MergeResult,
    ):
        """删除源目录中已不存在的应用（source-of-truth）"""
        orphan_keys = [key for key in all_apps.keys() if key not in source_keys]
        for key in orphan_keys:
            self.logger.info(f"  ✓ 删除孤儿应用 '{key}'")
            del all_apps[key]
            result.removed_count += 1

    @staticmethod
    def _compare_apps(app1: AppInfo, app2: AppInfo) -> List[str]:
        """比较两个应用信息，返回差异字段列表"""
        differences = []
        app1_dict = app1.to_dict()
        app2_dict = app2.to_dict()
        all_keys = set(app1_dict.keys()) | set(app2_dict.keys())

        for key in all_keys:
            if app1_dict.get(key) != app2_dict.get(key):
                differences.append(key)

        return differences

    def _save_all_json(
        self,
        all_apps: Dict[str, AppInfo],
        metadata: Dict,
        result: MergeResult,
    ):
        """保存all.json文件"""
        try:
            apps_data = []
            for app in all_apps.values():
                app_dict = app.to_dict()
                ok, err = AppValidator.validate_app_info(app_dict)
                if not ok:
                    self.logger.warning(
                        f"写出前校验失败，仍保留条目: {app.get_key()} ({err})"
                    )
                apps_data.append(app_dict)

            apps_data.sort(key=lambda x: (x.get("name") or "").lower())

            all_data = {**metadata, "apps": apps_data}

            success = self.json_handler.save(self.paths.all_json, all_data)
            if success:
                result.total_apps = len(all_apps)
                self.logger.info(f"✓ 文件已保存到 {self.paths.all_json}")
            else:
                result.success = False

        except Exception as e:
            self.logger.error("保存all.json失败", exception=e)
            result.success = False

    def _print_statistics(self, result: MergeResult):
        """打印统计信息"""
        print("\n" + "=" * 80)
        print("合并统计:")
        print(f"  ✓ 新增应用: {result.added_count} 个")
        print(f"  ✓ 更新应用: {result.updated_count} 个")
        print(f"  ✓ 删除孤儿: {result.removed_count} 个")
        print(f"  - 未变化: {result.unchanged_count} 个")
        print(f"  总计: {result.total_apps} 个应用")
        print("=" * 80)
