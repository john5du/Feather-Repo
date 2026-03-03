import json
from pathlib import Path


def load_json(filename):
    """加载JSON文件"""
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(filename, data):
    """保存JSON文件"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_app_key(app):
    """获取应用的唯一标识 - 优先使用name，其次使用bundleIdentifier"""
    if isinstance(app, dict):
        return app.get('name', '') or app.get('bundleIdentifier', '')
    return ''


def merge_apps():
    """合并应用信息"""

    # 要处理的三个JSON文件
    source_files = ['fluxdo.json', 'kazumi.json', 'piliplus.json']
    all_file = 'all.json'

    # 加载all.json
    all_data = load_json(all_file)

    # 确保apps是列表
    if not isinstance(all_data.get('apps'), list):
        all_data['apps'] = []

    # 创建应用字典（用于快速查找和更新）
    all_apps = {get_app_key(app): app for app in all_data.get('apps', [])}

    print(f"初始 all.json 中有 {len(all_apps)} 个应用")
    print("=" * 60)

    # 遍历每个源文件
    for source_file in source_files:
        try:
            source_data = load_json(source_file)

            # 确保apps是列表
            if not isinstance(source_data.get('apps'), list):
                print(f"警告: {source_file} 中的apps不是列表，跳过")
                continue

            source_apps = source_data.get('apps', [])

            print(f"\n处理 {source_file}...")
            print(f"  源文件中有 {len(source_apps)} 个应用")

            for app in source_apps:
                # 验证app是字典
                if not isinstance(app, dict):
                    print(f"  警告: 应用数据格式错误，跳过")
                    continue

                app_key = get_app_key(app)
                if not app_key:
                    print(f"  警告: 无法获取应用标识，跳过")
                    continue

                source_version = app.get('version', '未知')

                if app_key in all_apps:
                    # 应用已存在，检查版本
                    all_version = all_apps[app_key].get('version', '未知')
                    if source_version != all_version:
                        print(f"  ✓ 更新应用 '{app_key}': {all_version} -> {source_version}")
                        all_apps[app_key] = app
                    else:
                        print(f"  - 应用 '{app_key}' 版本相同 ({source_version})，跳过")
                else:
                    # 应用不存在，添加
                    print(f"  ✓ 添加新应用 '{app_key}' (版本: {source_version})")
                    all_apps[app_key] = app

        except FileNotFoundError:
            print(f"✗ 错误: 文件 {source_file} 不存在，跳过")
        except json.JSONDecodeError as e:
            print(f"✗ 错误: 文件 {source_file} JSON格式错误 - {e}，跳过")
        except Exception as e:
            print(f"✗ 错误: 处理 {source_file} 时出错 - {e}，跳过")

    # 更新all.json中的apps列表
    all_data['apps'] = list(all_apps.values())
    save_json(all_file, all_data)

    print("\n" + "=" * 60)
    print(f"✓ 合并完成！all.json 现在有 {len(all_apps)} 个应用")
    print(f"✓ 文件已保存到 {all_file}")


if __name__ == '__main__':
    merge_apps()