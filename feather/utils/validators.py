"""数据验证工具"""

from typing import Dict, Any, Tuple, Optional


class AppValidator:
    """应用信息验证器"""

    REQUIRED_FIELDS = {
        'name',
        'bundleIdentifier',
        'version',
        'versionDate',
        'downloadURL',
        'size',
    }

    @staticmethod
    def validate_app_info(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        验证应用信息

        Args:
            data: 应用数据

        Returns:
            (是否有效, 错误信息)
        """
        if not isinstance(data, dict):
            return False, "应用数据必须是字典"

        # 检查必需字段
        missing_fields = AppValidator.REQUIRED_FIELDS - set(data.keys())
        if missing_fields:
            return False, f"缺少必需字段: {', '.join(missing_fields)}"

        # 验证字段类型
        if not isinstance(data.get('name'), str):
            return False, "name 必须是字符串"

        if not isinstance(data.get('bundleIdentifier'), str):
            return False, "bundleIdentifier 必须是字符串"

        if not isinstance(data.get('size'), int):
            return False, "size 必须是整数"

        return True, None

    @staticmethod
    def validate_json_structure(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        验证JSON结构

        Args:
            data: JSON数据

        Returns:
            (是否有效, 错误信息)
        """
        if not isinstance(data, dict):
            return False, "数据必须是字典"

        if 'apps' not in data:
            return False, "缺少 'apps' 键"

        if not isinstance(data['apps'], list):
            return False, "'apps' 必须是列表"

        return True, None


class VersionValidator:
    """版本信息验证器"""

    @staticmethod
    def validate_version_format(version: str) -> Tuple[bool, Optional[str]]:
        """
        验证版本号格式

        Args:
            version: 版本号字符串

        Returns:
            (是否有效, 错误信息)
        """
        if not isinstance(version, str):
            return False, "版本号必须是字符串"

        if not version.strip():
            return False, "版本号不能为空"

        # 简单的版本号格式检查（允许1.0, 1.0.0, 1.0.0-beta等）
        parts = version.split('.')
        if len(parts) < 2:
            return False, "版本号格式不正确（例如：1.0.0）"

        return True, None

    @staticmethod
    def validate_version_array(versions: list) -> Tuple[bool, Optional[str]]:
        """
        验证版本数组

        Args:
            versions: 版本数组

        Returns:
            (是否有效, 错误信息)
        """
        if not isinstance(versions, list):
            return False, "versions 必须是列表"

        if len(versions) > 20:
            return False, f"versions 数组超过限制（最多20个，实际{len(versions)}个）"

        for i, version in enumerate(versions):
            if not isinstance(version, dict):
                return False, f"版本 {i} 不是字典"

            required = {'version', 'date', 'downloadURL', 'size'}
            if not required.issubset(set(version.keys())):
                return False, f"版本 {i} 缺少必需字段"

        return True, None


class URLValidator:
    """URL验证器"""

    @staticmethod
    def validate_download_url(url: str) -> Tuple[bool, Optional[str]]:
        """
        验证下载URL

        Args:
            url: URL字符串

        Returns:
            (是否有效, 错误信息)
        """
        if not isinstance(url, str):
            return False, "URL必须是字符串"

        if not url.strip():
            return False, "URL不能为空"

        if not (url.startswith('http://') or url.startswith('https://')):
            return False, "URL必须以 http:// 或 https:// 开头"

        return True, None
