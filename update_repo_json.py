import json
import os
from datetime import datetime
from github import Github
import requests

def get_file_size(url):
    response = requests.head(url)
    return int(response.headers.get('content-length', 0))

def main():
    github_token = os.environ['GITHUB_TOKEN']
    repo_owner = os.environ['REPO_OWNER']
    repo_name = os.environ['REPO_NAME']
    json_file_name = os.environ['JSON_FILE']
    # initial_json_func_name = os.environ.get('INITIAL_JSON_FUNCTION', 'None') # 不再需要，因为kazumi不创建

    # 定义输出文件路径
    github_output_path = os.environ.get('GITHUB_OUTPUT')
    
    def set_github_output(name, value):
        if github_output_path:
            with open(github_output_path, 'a') as f:
                f.write(f"{name}={value}\n")
        else:
            print(f"Warning: GITHUB_OUTPUT environment variable not found. Cannot set output '{name}'.")


    g = Github(github_token)
    repo = g.get_repo(f"{repo_owner}/{repo_name}")
    
    latest_release = repo.get_latest_release()
    
    ipa_asset = None
    for asset in latest_release.get_assets():
        if asset.name.endswith('.ipa'):
            ipa_asset = asset
            break
    
    if not ipa_asset:
        print(f"[{json_file_name}] No IPA file found in latest release for {repo_owner}/{repo_name}. Skipping update.")
        set_github_output("updated", "false") # 更新输出
        return
    
    source_data = {}
    
    if os.path.exists(json_file_name):
        try:
            with open(json_file_name, 'r', encoding='utf-8') as f:
                source_data = json.load(f)
            print(f"[{json_file_name}] Loaded existing data.")
        except (FileNotFoundError, json.JSONDecodeError):
            print(f"[{json_file_name}] Existing {json_file_name} is invalid or not found. Cannot proceed for Kazumi (no initial creation func).")
            set_github_output("updated", "false") # 更新输出
            return
    else:
        print(f"[{json_file_name}] {json_file_name} not found locally. Cannot proceed for Kazumi (no initial creation func).")
        set_github_output("updated", "false") # 更新输出
        return

    if 'apps' not in source_data or not source_data['apps']:
        print(f"[{json_file_name}] 'apps' array not found or is empty in {json_file_name}.")
        set_github_output("updated", "false") # 更新输出
        return

    app_data = source_data['apps'][0]
    
    current_version = app_data.get('version', '')
    new_version = latest_release.tag_name.lstrip('v')
    current_download_url = app_data.get('downloadURL','')
    new_download_url = ipa_asset.browser_download_url


    if current_version == new_version and current_download_url == new_download_url:
        print(f"[{json_file_name}] Current version '{current_version}' is already the latest with same download URL. No update needed.")
        set_github_output("updated", "false") # 更新输出
        return

    app_data.update({
        'version': new_version,
        'versionDate': latest_release.published_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        'downloadURL': new_download_url,
        'size': ipa_asset.size,
        'versionDescription': latest_release.body
    })
    print(f"[{json_file_name}] Updated version to: {new_version}")

    with open(json_file_name, 'w', encoding='utf-8') as f:
        json.dump(source_data, f, ensure_ascii=False, indent=2)
    print(f"[{json_file_name}] Successfully updated {json_file_name}")
    set_github_output("updated", "true") # 更新输出

if __name__ == '__main__':
    main()
