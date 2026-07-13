"""数据格式化工具"""

import re
from typing import Any


class ReleaseInfoExtractor:
    """GitHub Release信息提取器"""

    _LEADING_V = re.compile(r"^[vV]+")
    _SUFFIXES = ("-release", "-stable", "-final")

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

        separators = ["<div", "---", "\n\n"]

        for separator in separators:
            if separator in body:
                extracted = body.split(separator)[0].strip()
                if extracted:
                    return extracted[:500]

        return body[:500].strip()

    @staticmethod
    def extract_version_from_tag(tag_name: str) -> str:
        """
        从GitHub tag提取版本号

        - 去掉前导 v/V
        - 去掉 -release/-stable/-final
        - 去掉 +build 后缀
        """
        if not tag_name:
            return ""

        version = ReleaseInfoExtractor._LEADING_V.sub("", tag_name.strip())

        lower = version.lower()
        for suffix in ReleaseInfoExtractor._SUFFIXES:
            if lower.endswith(suffix):
                version = version[: -len(suffix)]
                break

        if "+" in version:
            version = version.split("+", 1)[0]

        return version.strip()

    @staticmethod
    def format_iso_date(date_obj: Any) -> str:
        """格式化日期为ISO格式 (YYYY-MM-DDTHH:MM:SSZ)"""
        if not hasattr(date_obj, "isoformat"):
            return ""

        iso_str = date_obj.isoformat()

        if not iso_str.endswith("Z"):
            iso_str = iso_str.replace("+00:00", "Z")

        return iso_str

    @staticmethod
    def format_date_short(date_obj: Any) -> str:
        """格式化日期为短格式 (YYYY-MM-DD)"""
        if not hasattr(date_obj, "strftime"):
            return ""

        return date_obj.strftime("%Y-%m-%d")
