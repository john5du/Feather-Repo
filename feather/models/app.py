"""应用数据模型"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


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
    _field_order: List[str] = field(default_factory=list, repr=False)

    REQUIRED_KEYS = {"version", "date", "downloadURL", "size"}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，尽量保持原字段顺序"""
        data = {
            "version": self.version,
            "date": self.date,
            "downloadURL": self.downloadURL,
            "size": self.size,
            "minOSVersion": self.minOSVersion,
            "localizedDescription": self.localizedDescription,
        }
        data.update(self.extra_fields)

        present = set(self._field_order)
        filtered: Dict[str, Any] = {}
        for key, value in data.items():
            if key in self.REQUIRED_KEYS:
                filtered[key] = value
            elif key in self.extra_fields:
                filtered[key] = value
            elif key in present:
                filtered[key] = value

        return _order_dict(filtered, self._field_order)

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
            _field_order=list(data.keys()),
        )


@dataclass
class AppInfo:
    """应用信息（字段名对齐 Feather 源格式）"""
    name: str
    bundleIdentifier: str
    version: str
    versionDate: str
    downloadURL: str
    size: int
    versions: List[VersionEntry] = field(default_factory=list)
    category: str = ""
    developerName: str = ""
    iconURL: str = ""
    subtitle: str = ""
    localizedDescription: str = ""
    versionDescription: str = ""
    changelog: str = ""
    minOSVersion: str = "13.0"
    tintColor: str = ""
    extra_fields: Dict[str, Any] = field(default_factory=dict)
    _field_order: List[str] = field(default_factory=list, repr=False)
    _present_keys: set = field(default_factory=set, repr=False)

    KNOWN_KEYS = {
        "name",
        "bundleIdentifier",
        "version",
        "versionDate",
        "downloadURL",
        "size",
        "versions",
        "category",
        "developerName",
        "iconURL",
        "subtitle",
        "localizedDescription",
        "versionDescription",
        "changelog",
        "minOSVersion",
        "tintColor",
    }

    REQUIRED_KEYS = {
        "version",
        "versionDate",
        "downloadURL",
        "size",
        "bundleIdentifier",
        "name",
        "versions",
    }

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，尽量保持原字段顺序与已有键"""
        data: Dict[str, Any] = {
            "name": self.name,
            "bundleIdentifier": self.bundleIdentifier,
            "version": self.version,
            "versionDate": self.versionDate,
            "downloadURL": self.downloadURL,
            "size": self.size,
            "category": self.category,
            "developerName": self.developerName,
            "iconURL": self.iconURL,
            "subtitle": self.subtitle,
            "localizedDescription": self.localizedDescription,
            "versionDescription": self.versionDescription,
            "changelog": self.changelog,
            "minOSVersion": self.minOSVersion,
            "tintColor": self.tintColor,
            "versions": [item.to_dict() for item in self.versions],
        }
        data.update(self.extra_fields)

        present = self._present_keys or set(self._field_order)
        filtered: Dict[str, Any] = {}
        for key, value in data.items():
            if key in self.REQUIRED_KEYS:
                filtered[key] = value
            elif key in self.extra_fields:
                filtered[key] = value
            elif key in present:
                filtered[key] = value
            # 未出现过的可选已知字段不因默认值而注入，避免无意义 diff

        return _order_dict(filtered, self._field_order)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppInfo":
        """从字典创建实例，兼容旧字段名"""
        versions: List[VersionEntry] = []
        if "versions" in data and isinstance(data["versions"], list):
            versions = [
                VersionEntry.from_dict(item)
                for item in data["versions"]
                if isinstance(item, dict)
            ]

        # 兼容旧字段 developer / icon
        developer_name = data.get("developerName")
        if developer_name is None:
            developer_name = data.get("developer", "")
        icon_url = data.get("iconURL")
        if icon_url is None:
            icon_url = data.get("icon", "")

        known_keys = set(cls.KNOWN_KEYS) | {"developer", "icon"}
        extra_fields = {
            key: value for key, value in data.items() if key not in known_keys
        }
        # 旧字段已映射到新字段时，不再放入 extra
        extra_fields.pop("developer", None)
        extra_fields.pop("icon", None)

        present_keys = set(data.keys())
        # 记录映射后的标准键
        if "developer" in present_keys and "developerName" not in present_keys:
            present_keys.add("developerName")
            present_keys.discard("developer")
        if "icon" in present_keys and "iconURL" not in present_keys:
            present_keys.add("iconURL")
            present_keys.discard("icon")

        field_order = []
        for key in data.keys():
            if key == "developer":
                field_order.append("developerName")
            elif key == "icon":
                field_order.append("iconURL")
            else:
                field_order.append(key)

        return cls(
            name=data.get("name", ""),
            bundleIdentifier=data.get("bundleIdentifier", ""),
            version=data.get("version", ""),
            versionDate=data.get("versionDate", ""),
            downloadURL=data.get("downloadURL", ""),
            size=data.get("size", 0),
            versions=versions,
            category=data.get("category", ""),
            developerName=developer_name or "",
            iconURL=icon_url or "",
            subtitle=data.get("subtitle", ""),
            localizedDescription=data.get("localizedDescription", ""),
            versionDescription=data.get("versionDescription", ""),
            changelog=data.get("changelog", ""),
            minOSVersion=data.get("minOSVersion", "13.0"),
            tintColor=data.get("tintColor", ""),
            extra_fields=extra_fields,
            _field_order=field_order,
            _present_keys=present_keys,
        )

    def get_key(self) -> str:
        """获取应用的唯一标识（优先 bundleIdentifier）"""
        return self.bundleIdentifier or self.name

    def has_same_version_info(self, other: "AppInfo") -> bool:
        """检查版本信息是否相同"""
        return (
            self.version == other.version
            and self.versionDate == other.versionDate
            and self.downloadURL == other.downloadURL
            and self.size == other.size
        )

    def mark_fields_present(self, *keys: str) -> None:
        """标记字段在写出时必须保留"""
        self._present_keys.update(keys)
        for key in keys:
            if key not in self._field_order:
                self._field_order.append(key)


def _order_dict(data: Dict[str, Any], field_order: Optional[List[str]]) -> Dict[str, Any]:
    """按原顺序输出字典，未知新键追加在末尾"""
    if not field_order:
        return dict(data)

    ordered: Dict[str, Any] = {}
    for key in field_order:
        if key in data:
            ordered[key] = data[key]
    for key, value in data.items():
        if key not in ordered:
            ordered[key] = value
    return ordered
