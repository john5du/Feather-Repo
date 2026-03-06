"""日志系统"""

from datetime import datetime
from enum import Enum
from typing import Optional, Any, Dict


class LogLevel(Enum):
    """日志级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class FeatherLogger:
    """结构化日志记录器"""

    def __init__(self, level: LogLevel = LogLevel.INFO):
        """
        初始化日志记录器

        Args:
            level: 日志级别
        """
        self.level = level
        self.level_order = {
            LogLevel.DEBUG: 0,
            LogLevel.INFO: 1,
            LogLevel.WARNING: 2,
            LogLevel.ERROR: 3,
        }

    def debug(self, message: str, context: Optional[Dict[str, Any]] = None):
        """记录调试日志"""
        self._log(LogLevel.DEBUG, message, context)

    def info(self, message: str, context: Optional[Dict[str, Any]] = None):
        """记录信息日志"""
        self._log(LogLevel.INFO, message, context)

    def warning(self, message: str, context: Optional[Dict[str, Any]] = None):
        """记录警告日志"""
        self._log(LogLevel.WARNING, message, context)

    def error(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None
    ):
        """记录错误日志"""
        if exception:
            context = context or {}
            context['exception'] = str(exception)
            context['exception_type'] = type(exception).__name__
        self._log(LogLevel.ERROR, message, context)

    def _log(
        self,
        level: LogLevel,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        内部日志记录方法

        Args:
            level: 日志级别
            message: 日志消息
            context: 上下文信息
        """
        # 检查日志级别
        if self.level_order[level] < self.level_order[self.level]:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        level_str = level.value.ljust(7)

        # 构建日志行
        log_line = f"[{timestamp}] {level_str} {message}"

        # 添加上下文信息
        if context:
            context_str = " | ".join(
                f"{k}={v}" for k, v in context.items()
            )
            log_line += f" | {context_str}"

        print(log_line)

    @staticmethod
    def setup(level_str: str = "INFO") -> "FeatherLogger":
        """
        创建日志记录器实例

        Args:
            level_str: 日志级别字符串（DEBUG/INFO/WARNING/ERROR）

        Returns:
            日志记录器实例
        """
        try:
            level = LogLevel[level_str.upper()]
        except KeyError:
            level = LogLevel.INFO

        return FeatherLogger(level)
