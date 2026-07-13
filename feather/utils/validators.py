"""数据验证工具"""

from typing import Any, Dict, List, Optional, Tuple


class AppValidator:
    """应用信息验证器"""

    REQUIRED_FIELDS = {
        "name",
        "bundleIdentifier",
        "version",
        "versionDate",
        "downloadURL",
        "size",
    }

    @staticmethod
    def validate_app_info(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """验证应用信息"""
        if not isinstance(data, dict):
            return False, "应用数据必须是字典"

        missing_fields = AppValidator.REQUIRED_FIELDS - set(data.keys())
        if missing_fields:
            return False, f"缺少必需字段: {', '.join(sorted(missing_fields))}"

        if not isinstance(data.get("name"), str) or not data["name"].strip():
            return False, "name 必须是非空字符串"

        if not isinstance(data.get("bundleIdentifier"), str) or not data["bundleIdentifier"].strip():
            return False, "bundleIdentifier 必须是非空字符串"

        if not isinstance(data.get("version"), str) or not str(data["version"]).strip():
            return False, "version 必须是非空字符串"

        size = data.get("size")
        if not isinstance(size, int) or isinstance(size, bool) or size < 0:
            return False, "size 必须是非负整数"

        ok, err = URLValidator.validate_download_url(data.get("downloadURL", ""))
        if not ok:
            return False, err

        if "versions" in data:
            ok, err = VersionValidator.validate_version_array(data["versions"])
            if not ok:
                return False, err

        return True, None

    @staticmethod
    def validate_json_structure(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """验证JSON结构"""
        if not isinstance(data, dict):
            return False, "数据必须是字典"

        if "apps" not in data:
            return False, "缺少 'apps' 键"

        if not isinstance(data["apps"], list):
            return False, "'apps' 必须是列表"

        return True, None


class VersionValidator:
    """版本信息验证器"""

    @staticmethod
    def validate_version_format(version: str) -> Tuple[bool, Optional[str]]:
        """验证版本号格式"""
        if not isinstance(version, str):
            return False, "版本号必须是字符串"

        if not version.strip():
            return False, "版本号不能为空"

        return True, None

    @staticmethod
    def validate_version_array(versions: list) -> Tuple[bool, Optional[str]]:
        """验证版本数组"""
        if not isinstance(versions, list):
            return False, "versions 必须是列表"

        if len(versions) > 20:
            return False, f"versions 数组超过限制（最多20个，实际{len(versions)}个）"

        for i, version in enumerate(versions):
            if not isinstance(version, dict):
                return False, f"版本 {i} 不是字典"

            required = {"version", "date", "downloadURL", "size"}
            if not required.issubset(set(version.keys())):
                return False, f"版本 {i} 缺少必需字段"

            ok, err = URLValidator.validate_download_url(version.get("downloadURL", ""))
            if not ok:
                return False, f"版本 {i}: {err}"

        return True, None


class URLValidator:
    """URL验证器"""

    @staticmethod
    def validate_download_url(url: str) -> Tuple[bool, Optional[str]]:
        """验证下载URL"""
        if not isinstance(url, str):
            return False, "URL必须是字符串"

        if not url.strip():
            return False, "URL不能为空"

        if not (url.startswith("http://") or url.startswith("https://")):
            return False, "URL必须以 http:// 或 https:// 开头"

        return True, None
