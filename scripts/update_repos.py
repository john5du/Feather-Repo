"""
简化的更新脚本 - 使用新的feather包
"""

import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# 添加项目根目录到Python路径
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from feather.core.config import ConfigManager
from feather.core.logger import FeatherLogger
from feather.services.updater import RepositoryUpdater


def set_github_output(name: str, value: str):
    """设置GitHub Actions输出"""
    github_output_path = os.environ.get('GITHUB_OUTPUT')

    if github_output_path:
        try:
            with open(github_output_path, 'a') as f:
                f.write(f"{name}={value}\n")
        except Exception as e:
            print(f"警告: 无法设置GitHub输出 '{name}': {e}")
    else:
        # 本地运行时的备用方案
        print(f"[GitHub Output] {name}={value}")


def main():
    """主程序入口"""
    config = None
    logger = None
    try:
        # 固定工作目录为仓库根目录，避免相对路径受运行位置影响
        os.chdir(PROJECT_ROOT)

        config = ConfigManager.create()
        logger = FeatherLogger.setup(config.get_logging().level)

        logger.info("开始更新仓库...")
        config.print_summary()

        # 执行更新
        updater = RepositoryUpdater(config, logger)
        result = updater.update_all()

        # 设置GitHub Actions输出
        set_github_output(
            'updated',
            'true' if result.updated_count > 0 else 'false'
        )
        set_github_output(
            'files',
            ' '.join(result.updated_files)
        )

        # 返回状态码
        return 0 if result.success else 1

    except Exception as e:
        if logger:
            logger.error("更新失败", exception=e)
        else:
            print(f"✗ 更新失败: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
