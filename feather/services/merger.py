"""应用合并服务"""

from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from feather.core.json_handler import JSONHandler
from feather.core.logger import FeatherLogger
from feather.core.config import ConfigManager, PathConfig
from feather.models.app import AppInfo


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
    stats: List[MergeStat] = None

    def __post_init__(self):
        if self.stats is None:
            self.stats = []

    def to_dict(self) -> Dict:
        return {
            'success': self.success,
            'total_apps': self.total_apps,
            'added': self.added_count,
            'updated': self.updated_count,
            'unchanged': self.unchanged_count,
        }


class AppMerger:
    """应用合并服务"""

    def __init__(
        self,
        config: ConfigManager,
        logger: FeatherLogger,
        json_handler: JSONHandler = None
    ):
        """
        初始化AppMerger

        Args:
            config: 配置管理器
            logger: 日志记录器
            json_handler: JSON处理器（可选）
        """
        self.config = config
        self.logger = logger
        self.json_handler = json_handler or JSONHandler()
        self.paths = config.get_paths()

    def merge_all(self) -> MergeResult:
        """
        执行合并所有应用

        Returns:
            MergeResult 合并结果
        """
        result = MergeResult()

        try:
            # 扫描源文件
            source_files = self._scan_source_files()

            if not source_files:
                self.logger.warning("未找到任何JSON文件")
                result.success = False
                return result

            self.logger.info(f"发现 {len(source_files)} 个源文件")
            for sf in source_files:
                self.logger.info(f"  - {sf}")

            # 加载all.json
            all_app_list, metadata = self._load_all_json()
            all_apps: Dict[str, AppInfo] = {
                app.get_key(): app
                for app in all_app_list
            }

            self.logger.info(f"all.json 中已有 {len(all_apps)} 个应用")

            # 遍历源文件进行合并
            for source_file in source_files:
                self._merge_single_file(source_file, all_apps, result)

            # 保存合并结果
            self._save_all_json(all_apps, metadata, result)

            # 输出统计信息
            self._print_statistics(result)

            return result

        except Exception as e:
            self.logger.error("合并过程中发生错误", exception=e)
            result.success = False
            return result

    def _scan_source_files(self) -> List[str]:
        """
        扫描源文件

        Returns:
            源文件路径列表
        """
        app_dir = Path(self.paths.app_dir)
        source_files = []

        if not app_dir.exists():
            self.logger.warning(f"应用目录不存在: {app_dir}")
            return source_files

        for json_file in sorted(app_dir.glob('*.json')):
            if json_file.name != 'all.json':
                source_files.append(str(json_file))

        return source_files

    def _load_all_json(self) -> Tuple[List[AppInfo], Dict]:
        """
        加载all.json文件

        Returns:
            (应用列表, 外层元数据字典)
        """
        try:
            data = self.json_handler.load(self.paths.all_json)

            # 提取外层元数据（除了apps字段）
            metadata = {k: v for k, v in data.items() if k != 'apps'}
            apps_data = data.get('apps', [])

            apps = []
            for app_data in apps_data:
                try:
                    app = AppInfo.from_dict(app_data)
                    apps.append(app)
                except Exception as e:
                    self.logger.warning(
                        f"解析应用数据失败: {e}",
                        {'app_name': app_data.get('name', 'unknown')}
                    )

            return apps, metadata

        except FileNotFoundError:
            self.logger.warning(f"文件不存在: {self.paths.all_json}")
            return [], {}
        except Exception as e:
            self.logger.error(f"加载all.json失败", exception=e)
            return [], {}

    def _merge_single_file(
        self,
        source_file: str,
        all_apps: Dict[str, AppInfo],
        result: MergeResult
    ):
        """
        合并单个源文件

        Args:
            source_file: 源文件路径
            all_apps: 所有应用字典
            result: 合并结果对象
        """
        stat = MergeStat(file=source_file)

        try:
            source_data = self.json_handler.load(source_file)
            source_apps = source_data.get('apps', [])

            if not isinstance(source_apps, list):
                self.logger.warning(f"{source_file} 中apps不是列表")
                return

            self.logger.info(f"处理 {source_file} ({len(source_apps)} 个应用)")

            for app_data in source_apps:
                if not isinstance(app_data, dict):
                    self.logger.warning(f"  应用数据格式错误，跳过")
                    continue

                try:
                    app = AppInfo.from_dict(app_data)
                    app_key = app.get_key()

                    if not app_key:
                        self.logger.warning(f"  无法获取应用标识，跳过")
                        continue

                    if app_key in all_apps:
                        # 比较差异
                        diff = self._compare_apps(all_apps[app_key], app)
                        if diff:
                            self.logger.info(
                                f"  ✓ 更新应用 '{app_key}'",
                                {'changes': len(diff)}
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

    @staticmethod
    def _compare_apps(app1: AppInfo, app2: AppInfo) -> List[str]:
        """
        比较两个应用信息

        Returns:
            差异字段列表
        """
        differences = []

        # 比较所有字段
        app1_dict = app1.to_dict()
        app2_dict = app2.to_dict()

        all_keys = set(app1_dict.keys()) | set(app2_dict.keys())

        for key in all_keys:
            val1 = app1_dict.get(key)
            val2 = app2_dict.get(key)

            if val1 != val2:
                differences.append(key)

        return differences

    def _save_all_json(
        self,
        all_apps: Dict[str, AppInfo],
        metadata: Dict,
        result: MergeResult
    ):
        """
        保存all.json文件

        Args:
            all_apps: 所有应用字典
            metadata: 外层元数据
            result: 合并结果对象
        """
        try:
            # 转换为字典列表
            apps_data = [app.to_dict() for app in all_apps.values()]

            # 按name排序
            apps_data.sort(key=lambda x: x.get('name', ''))

            # 合并外层字段和apps数据
            all_data = {**metadata, 'apps': apps_data}

            success = self.json_handler.save(
                self.paths.all_json,
                all_data,
            )

            if success:
                result.total_apps = len(all_apps)
                self.logger.info(f"✓ 文件已保存到 {self.paths.all_json}")
            else:
                result.success = False

        except Exception as e:
            self.logger.error(f"保存all.json失败", exception=e)
            result.success = False

    def _print_statistics(self, result: MergeResult):
        """打印统计信息"""
        print("\n" + "=" * 80)
        print("合并统计:")
        print(f"  ✓ 新增应用: {result.added_count} 个")
        print(f"  ✓ 更新应用: {result.updated_count} 个")
        print(f"  - 未变化: {result.unchanged_count} 个")
        print(f"  总计: {result.total_apps} 个应用")
        print("=" * 80)
