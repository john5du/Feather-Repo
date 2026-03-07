"""JSON文件处理工具"""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


class JSONHandler:
    """统一的JSON加载/保存工具"""

    @staticmethod
    def load(filepath: str, encoding: str = 'utf-8') -> Dict[str, Any]:
        """
        加载JSON文件

        Args:
            filepath: JSON文件路径
            encoding: 文件编码

        Returns:
            JSON数据字典

        Raises:
            FileNotFoundError: 文件不存在
            json.JSONDecodeError: JSON格式错误
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"文件不存在: {filepath}")

        try:
            with open(filepath, 'r', encoding=encoding) as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"JSON格式错误 ({filepath}): {e.msg}",
                e.doc,
                e.pos
            )
        except Exception as e:
            raise Exception(f"读取JSON文件失败 ({filepath}): {str(e)}")

    @staticmethod
    def save(
        filepath: str,
        data: Dict[str, Any],
        encoding: str = 'utf-8',
        indent: int = 2
    ) -> bool:
        """
        保存JSON文件

        Args:
            filepath: JSON文件路径
            data: 要保存的数据
            encoding: 文件编码
            indent: JSON缩进

        Returns:
            是否保存成功
        """
        filepath = Path(filepath)

        try:
            # 确保目录存在
            filepath.parent.mkdir(parents=True, exist_ok=True)

            # 保存JSON
            with open(filepath, 'w', encoding=encoding) as f:
                json.dump(data, f, ensure_ascii=False, indent=indent)

            return True

        except Exception as e:
            print(f"✗ 保存JSON失败 ({filepath}): {str(e)}")
            return False

    @staticmethod
    def validate_structure(
        data: Dict[str, Any],
        required_keys: list = None
    ) -> Tuple[bool, Optional[str]]:
        """
        验证JSON结构

        Args:
            data: JSON数据
            required_keys: 必需的顶层键列表

        Returns:
            (是否有效, 错误信息)
        """
        if not isinstance(data, dict):
            return False, "数据必须是字典"

        if required_keys:
            missing_keys = [k for k in required_keys if k not in data]
            if missing_keys:
                return False, f"缺少必需键: {', '.join(missing_keys)}"

        return True, None

    @staticmethod
    def get_app_list(data: Dict[str, Any]) -> list:
        """
        从JSON数据中提取应用列表

        Args:
            data: JSON数据

        Returns:
            应用列表（如果不存在返回空列表）
        """
        apps = data.get('apps', [])
        if not isinstance(apps, list):
            return []
        return apps
