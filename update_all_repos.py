import json
import os
from datetime import datetime
from github import Github
import requests

def update_repo_json(repo_owner, repo_name, json_file_name):
    github_token = os.environ['GITHUB_TOKEN']
    g = Github(github_token)
    
    try:
        repo = g.get_repo(f"{repo_owner}/{repo_name}")
        latest_release = repo.get_latest_release()
        
        ipa_asset = None
        for asset in latest_release.get_assets():
            if asset.name.endswith('.ipa'):
                ipa_asset = asset
                break
        
        if not ipa_asset:
            print(f"[{json_file_name}] No IPA file found in latest release for {repo_owner}/{repo_name}. Skipping update.")
            return False
        
        # 读取现有JSON文件
        try:
            with open(json_file_name, 'r', encoding='utf-8') as f:
                source_data = json.load(f)
            print(f"[{json_file_name}] Loaded existing data.")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[{json_file_name}] Error reading {json_file_name}: {str(e)}")
            return False

        if 'apps' not in source_data or not source_data['apps']:
            print(f"[{json_file_name}] 'apps' array not found or is empty in {json_file_name}.")
            return False

        app_data = source_data['apps'][0]

        current_version = app_data.get('version', '')
        new_version = latest_release.tag_name.lstrip('v')
        current_download_url = app_data.get('downloadURL','')
        new_download_url = ipa_asset.browser_download_url

        if current_version == new_version and current_download_url == new_download_url:
            print(f"[{json_file_name}] Current version '{current_version}' is already the latest with same download URL. No update needed.")
            return False

        # 更新主要版本信息
        app_data.update({
            'version': new_version,
            'versionDate': latest_release.published_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            'downloadURL': new_download_url,
            'size': ipa_asset.size,
            'versionDescription': latest_release.body,
            'changelog': latest_release.body
        })

        # 更新或创建versions数组
        if 'versions' not in app_data:
            app_data['versions'] = []
        
        # 检查是否已存在该版本
        version_exists = any(v.get('version') == new_version for v in app_data['versions'])
        
        if not version_exists:
            # 添加新版本到versions数组开头
            new_version_entry = {
                'version': new_version,
                'date': latest_release.published_at.strftime("%Y-%m-%d"),
                'localizedDescription': latest_release.body,
                'downloadURL': new_download_url,
                'size': ipa_asset.size,
                'minOSVersion': app_data.get('minOSVersion', '13.0')
            }
            app_data['versions'].insert(0, new_version_entry)
            
            # 保持最多20个版本
            if len(app_data['versions']) > 20:
                app_data['versions'] = app_data['versions'][:20]

        print(f"[{json_file_name}] Updated version to: {new_version}")

        with open(json_file_name, 'w', encoding='utf-8') as f:
            json.dump(source_data, f, ensure_ascii=False, indent=2)
        print(f"[{json_file_name}] Successfully updated {json_file_name}")
        return True
        
    except Exception as e:
        print(f"[{json_file_name}] Error updating {json_file_name}: {str(e)}")
        return False

def main():
    github_output_path = os.environ.get('GITHUB_OUTPUT')
    
    def set_github_output(name, value):
        if github_output_path:
            with open(github_output_path, 'a') as f:
                f.write(f"{name}={value}\n")
        else:
            print(f"Warning: GITHUB_OUTPUT environment variable not found. Cannot set output '{name}'.")

    updated_files = []
    
    # 更新 Kazumi
    print("=== Updating Kazumi ===")
    if update_repo_json("Predidit", "Kazumi", "kazumi.json"):
        updated_files.append("kazumi.json")
    
    # 更新 PiliPlus
    print("\n=== Updating PiliPlus ===")
    if update_repo_json("bggRGjQaUbCoE", "PiliPlus", "piliplus.json"):
        updated_files.append("piliplus.json")
    
    if updated_files:
        print(f"\nUpdated files: {', '.join(updated_files)}")
        set_github_output("updated", "true")
        set_github_output("files", " ".join(updated_files))
    else:
        print("\nNo files were updated.")
        set_github_output("updated", "false")

if __name__ == '__main__':
    main()
