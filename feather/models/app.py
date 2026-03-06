"""应用数据模型"""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class VersionEntry:
    """版本条目"""
    version: str
    date: str
    downloadURL: str
    size: int
    minOSVersion: str = "13.0"
    localizedDescription: str = ""
    extra_fields: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = {
            "version": self.version,
            "date": self.date,
            "downloadURL": self.downloadURL,
            "size": self.size,
            "minOSVersion": self.minOSVersion,
            "localizedDescription": self.localizedDescription,
        }
        data.update(self.extra_fields)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VersionEntry":
        """从字典创建实例"""
        known_keys = {
            "version",
            "date",
            "downloadURL",
            "size",
            "minOSVersion",
            "localizedDescription",
        }
        extra_fields = {
            key: value for key, value in data.items() if key not in known_keys
        }

        return cls(
            version=data.get("version", ""),
            date=data.get("date", ""),
            downloadURL=data.get("downloadURL", ""),
            size=data.get("size", 0),
            minOSVersion=data.get("minOSVersion", "13.0"),
            localizedDescription=data.get("localizedDescription", ""),
            extra_fields=extra_fields,
        )


@dataclass
class AppInfo:
    """应用信息"""
    name: str
    bundleIdentifier: str
    version: str
    versionDate: str
    downloadURL: str
    size: int
    versions: List[VersionEntry] = field(default_factory=list)
    category: str = ""
    developer: str = ""
    icon: str = ""
    versionDescription: str = ""
    changelog: str = ""
    minOSVersion: str = "13.0"
    extra_fields: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = {
            "name": self.name,
            "bundleIdentifier": self.bundleIdentifier,
            "version": self.version,
            "versionDate": self.versionDate,
            "downloadURL": self.downloadURL,
            "size": self.size,
            "category": self.category,
            "developer": self.developer,
            "icon": self.icon,
            "versionDescription": self.versionDescription,
            "changelog": self.changelog,
            "minOSVersion": self.minOSVersion,
            "versions": [item.to_dict() for item in self.versions],
        }
        data.update(self.extra_fields)

        required_keys = {
            "version",
            "versionDate",
            "downloadURL",
            "size",
            "bundleIdentifier",
            "name",
            "versions",
        }
        extra_keys = set(self.extra_fields.keys())
        return {
            key: value
            for key, value in data.items()
            if value or key in required_keys or key in extra_keys
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppInfo":
        """从字典创建实例"""
        versions: List[VersionEntry] = []
        if "versions" in data and isinstance(data["versions"], list):
            versions = [
                VersionEntry.from_dict(item)
                for item in data["versions"]
                if isinstance(item, dict)
            ]

        known_keys = {
            "name",
            "bundleIdentifier",
            "version",
            "versionDate",
            "downloadURL",
            "size",
            "versions",
            "category",
            "developer",
            "icon",
            "versionDescription",
            "changelog",
            "minOSVersion",
        }
        extra_fields = {
            key: value for key, value in data.items() if key not in known_keys
        }

        return cls(
            name=data.get("name", ""),
            bundleIdentifier=data.get("bundleIdentifier", ""),
            version=data.get("version", ""),
            versionDate=data.get("versionDate", ""),
            downloadURL=data.get("downloadURL", ""),
            size=data.get("size", 0),
            versions=versions,
            category=data.get("category", ""),
            developer=data.get("developer", ""),
            icon=data.get("icon", ""),
            versionDescription=data.get("versionDescription", ""),
            changelog=data.get("changelog", ""),
            minOSVersion=data.get("minOSVersion", "13.0"),
            extra_fields=extra_fields,
        )

    def get_key(self) -> str:
        """获取应用的唯一标识"""
        return self.name or self.bundleIdentifier

    def has_same_version_info(self, other: "AppInfo") -> bool:
        """检查版本信息是否相同"""
        return (
            self.version == other.version
            and self.versionDate == other.versionDate
            and self.downloadURL == other.downloadURL
            and self.size == other.size
        )
