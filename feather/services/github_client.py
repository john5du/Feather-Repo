"""GitHub API客户端"""

import os
from typing import Optional, List, Dict, Any
from github import Github
from github.GithubException import GithubException


class GitHubClient:
    """GitHub API客户端封装"""

    def __init__(self, token: Optional[str] = None):
        """
        初始化GitHub客户端

        Args:
            token: GitHub Token，如果为None则从环境变量读取

        Raises:
            ValueError: Token为空
        """
        self.token = token or os.environ.get('GITHUB_TOKEN')

        if not self.token:
            raise ValueError(
                "GitHub Token未提供。"
                "请通过参数传递或设置 GITHUB_TOKEN 环境变量"
            )

        self.client = Github(self.token)

    def get_latest_release(self, owner: str, repo: str):
        """
        获取仓库的最新Release

        Args:
            owner: 仓库所有者
            repo: 仓库名称

        Returns:
            Release对象

        Raises:
            GithubException: GitHub API调用失败
        """
        try:
            repo_obj = self.client.get_repo(f"{owner}/{repo}")
            return repo_obj.get_latest_release()
        except GithubException as e:
            raise GithubException(
                e.status,
                f"获取 {owner}/{repo} 的最新Release失败: {e.data.get('message', str(e))}"
            )

    def get_ipa_assets(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """
        获取最新Release中的IPA文件

        Args:
            owner: 仓库所有者
            repo: 仓库名称

        Returns:
            IPA资源列表

        Raises:
            GithubException: GitHub API调用失败
        """
        try:
            latest_release = self.get_latest_release(owner, repo)
            ipa_assets = []

            for asset in latest_release.get_assets():
                if asset.name.endswith('.ipa'):
                    ipa_assets.append({
                        'name': asset.name,
                        'url': asset.browser_download_url,
                        'size': asset.size,
                        'download_count': asset.download_count,
                    })

            return ipa_assets

        except GithubException as e:
            raise e

    def extract_release_info(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        提取Release的关键信息

        Args:
            owner: 仓库所有者
            repo: 仓库名称

        Returns:
            Release信息字典

        Raises:
            GithubException: GitHub API调用失败
        """
        try:
            release = self.get_latest_release(owner, repo)

            return {
                'tag_name': release.tag_name,
                'version': release.tag_name.lstrip('v'),
                'published_at': release.published_at,
                'body': release.body,
                'prerelease': release.prerelease,
                'draft': release.draft,
                'assets': [
                    {
                        'name': asset.name,
                        'url': asset.browser_download_url,
                        'size': asset.size,
                    }
                    for asset in release.get_assets()
                ],
            }

        except GithubException as e:
            raise e

    def validate_connection(self) -> bool:
        """
        验证GitHub连接

        Returns:
            连接是否有效
        """
        try:
            # 尝试获取认证用户信息
            self.client.get_user()
            return True
        except Exception:
            return False
