"""
简化的合并脚本 - 使用新的feather包
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# 添加项目根目录到Python路径，确保可导入本地 feather 包
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from feather.core.config import ConfigManager
from feather.core.logger import FeatherLogger
from feather.services.merger import AppMerger


def main():
    """主程序入口"""
    logger = None
    try:
        # 修复 Windows 控制台默认编码导致的 Unicode 输出错误
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")

        # 固定工作目录为仓库根目录，避免相对路径受运行位置影响
        os.chdir(PROJECT_ROOT)

        config = ConfigManager.create()
        logger = FeatherLogger.setup(config.get_logging().level)

        logger.info("开始合并应用...")
        config.print_summary()

        # 执行合并
        merger = AppMerger(config, logger)
        result = merger.merge_all()

        # 返回状态码
        return 0 if result.success else 1

    except Exception as e:
        if logger:
            logger.error("合并失败", exception=e)
        else:
            print(f"✗ 合并失败: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
