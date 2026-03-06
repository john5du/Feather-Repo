"""数据格式化工具"""

from typing import Optional


class ReleaseInfoExtractor:
    """GitHub Release信息提取器"""

    @staticmethod
    def extract_description(body: str) -> str:
        """
        安全地从Release body提取描述

        Args:
            body: Release body文本

        Returns:
            提取的描述文本
        """
        if not body:
            return ""

        # 尝试多种分割方式
        separators = ['<div', '---', '\n\n']

        for separator in separators:
            if separator in body:
                extracted = body.split(separator)[0].strip()
                if extracted:
                    return extracted[:500]

        # 如果没有特殊分割符，返回前500个字符
        return body[:500].strip()

    @staticmethod
    def extract_version_from_tag(tag_name: str) -> str:
        """
        从GitHub tag提取版本号

        Args:
            tag_name: tag名称（如 v1.0.0）

        Returns:
            版本号（如 1.0.0）
        """
        if not tag_name:
            return ""

        # 移除前导 v
        version = tag_name.lstrip('v')

        # 移除后导的 -release, -stable等
        for suffix in ['-release', '-stable', '-final']:
            if version.endswith(suffix):
                version = version[:-len(suffix)]

        return version.strip()

    @staticmethod
    def format_iso_date(date_obj) -> str:
        """
        格式化日期为ISO格式

        Args:
            date_obj: Python datetime对象

        Returns:
            ISO格式日期字符串 (YYYY-MM-DDTHH:MM:SSZ)
        """
        if not hasattr(date_obj, 'isoformat'):
            return ""

        iso_str = date_obj.isoformat()

        # 确保以 Z 结尾（UTC）
        if not iso_str.endswith('Z'):
            iso_str = iso_str.replace('+00:00', 'Z')

        return iso_str

    @staticmethod
    def format_date_short(date_obj) -> str:
        """
        格式化日期为短格式

        Args:
            date_obj: Python datetime对象

        Returns:
            短格式日期字符串 (YYYY-MM-DD)
        """
        if not hasattr(date_obj, 'strftime'):
            return ""

        return date_obj.strftime("%Y-%m-%d")
