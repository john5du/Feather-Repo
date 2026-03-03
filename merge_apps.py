import json
from pathlib import Path
from typing import Any, Dict, List


def load_json(filename):
    """加载JSON文件"""
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(filename, data):
    """保存JSON文件"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_source_files():
    """扫描根目录下所有JSON文件（除了all.json）"""
    root_dir = Path('.')
    exclude_files = {'all.json'}

    json_files = []
    for json_file in root_dir.glob('*.json'):
        if json_file.name not in exclude_files:
            json_files.append(json_file.name)

    json_files.sort()  # 按字母顺序排序
    return json_files


def get_app_key(app):
    """获取应用的唯一标识 - 优先使用name，其次使用bundleIdentifier"""
    if isinstance(app, dict):
        return app.get('name', '') or app.get('bundleIdentifier', '')
    return ''


def compare_apps(app1: Dict, app2: Dict) -> tuple[bool, List[str]]:
    """
    比较两个应用的信息，返回(是否相同, 差异字段列表)
    """
    if not isinstance(app1, dict) or not isinstance(app2, dict):
        return False, ["数据类型不匹配"]

    differences = []

    # 获取两个应用的所有键
    all_keys = set(app1.keys()) | set(app2.keys())

    for key in all_keys:
        val1 = app1.get(key)
        val2 = app2.get(key)

        # 比较值
        if val1 != val2:
            differences.append(key)

    is_same = len(differences) == 0
    return is_same, differences


def get_diff_summary(app1: Dict, app2: Dict, diff_keys: List[str]) -> str:
    """生成差异摘要"""
    summary_parts = []

    # 优先显示重要字段的差异
    important_fields = ['version', 'versionDate', 'downloadURL', 'size']

    for field in important_fields:
        if field in diff_keys:
            val1 = app1.get(field)
            val2 = app2.get(field)

            # 对于长字符串，只显示前50个字符
            if isinstance(val1, str) and len(str(val1)) > 50:
                val1_str = str(val1)[:50] + "..."
            else:
                val1_str = val1

            if isinstance(val2, str) and len(str(val2)) > 50:
                val2_str = str(val2)[:50] + "..."
            else:
                val2_str = val2

            summary_parts.append(f"{field}: {val1_str} -> {val2_str}")

    # 显示其他差异字段（只显示字段名）
    other_diffs = [k for k in diff_keys if k not in important_fields]
    if other_diffs:
        summary_parts.append(f"其他字段: {', '.join(other_diffs)}")

    return ", ".join(summary_parts)


def merge_apps():
    """合并应用信息"""

    all_file = 'all.json'

    # 动态扫描源文件
    source_files = get_source_files()

    if not source_files:
        print(f"✗ 错误: 未找到任何JSON文件来处理")
        return

    print(f"发现 {len(source_files)} 个源文件:")
    for sf in source_files:
        print(f"  - {sf}")

    # 加载all.json
    all_data = load_json(all_file)

    # 确保apps是列表
    if not isinstance(all_data.get('apps'), list):
        all_data['apps'] = []

    # 创建应用字典（用于快速查找和更新）
    all_apps = {get_app_key(app): app for app in all_data.get('apps', [])}

    print(f"\n初始 all.json 中有 {len(all_apps)} 个应用")
    print("=" * 80)

    updated_count = 0
    added_count = 0
    unchanged_count = 0

    # 遍历每个源文件
    for source_file in source_files:
        try:
            source_data = load_json(source_file)

            # 确保apps是列表
            if not isinstance(source_data.get('apps'), list):
                print(f"✗ 警告: {source_file} 中的apps不是列表，跳过")
                continue

            source_apps = source_data.get('apps', [])

            print(f"\n处理 {source_file}...")
            print(f"  源文件中有 {len(source_apps)} 个应用")

            for app in source_apps:
                # 验证app是字典
                if not isinstance(app, dict):
                    print(f"  ✗ 应用数据格式错误，跳过")
                    continue

                app_key = get_app_key(app)
                if not app_key:
                    print(f"  ✗ 无法获取应用标识，跳过")
                    continue

                app_version = app.get('version', '未知')

                if app_key in all_apps:
                    # 应用已存在，比较所有信息
                    is_same, diff_keys = compare_apps(all_apps[app_key], app)

                    if not is_same:
                        # 存在差异，进行更新
                        diff_summary = get_diff_summary(all_apps[app_key], app, diff_keys)
                        print(f"  ✓ 更新应用 '{app_key}'")
                        print(f"    差异字段: {diff_summary}")
                        all_apps[app_key] = app
                        updated_count += 1
                    else:
                        # 信息完全相同，跳过
                        print(f"  - 应用 '{app_key}' (v{app_version}) 信息相同，无需更新")
                        unchanged_count += 1
                else:
                    # 应用不存在，添加
                    print(f"  ✓ 添加新应用 '{app_key}' (版本: {app_version})")
                    all_apps[app_key] = app
                    added_count += 1

        except FileNotFoundError:
            print(f"✗ 错误: 文件 {source_file} 不存在，跳过")
        except json.JSONDecodeError as e:
            print(f"✗ 错误: 文件 {source_file} JSON格式错误 - {e}，跳过")
        except Exception as e:
            print(f"✗ 错误: 处理 {source_file} 时出错 - {e}，跳过")

    # 更新all.json中的apps列表
    all_data['apps'] = list(all_apps.values())
    save_json(all_file, all_data)

    print("\n" + "=" * 80)
    print("合并统计:")
    print(f"  ✓ 新增应用: {added_count} 个")
    print(f"  ✓ 更新应用: {updated_count} 个")
    print(f"  - 未变化: {unchanged_count} 个")
    print(f"  总计: {len(all_apps)} 个应用")
    print(f"\n✓ 文件已保存到 {all_file}")


if __name__ == '__main__':
    merge_apps()