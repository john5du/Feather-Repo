"""GitHub API客户端"""

import os
import time
from typing import Any, Callable, Dict, List, Optional, TypeVar

from github import Github
from github.GithubException import GithubException, RateLimitExceededException

T = TypeVar("T")


class GitHubClient:
    """GitHub API客户端封装（含重试与限流处理）"""

    def __init__(self, token: Optional[str] = None, max_retries: int = 3):
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.max_retries = max(1, max_retries)

        if not self.token:
            raise ValueError(
                "GitHub Token未提供。"
                "请通过参数传递或设置 GITHUB_TOKEN 环境变量"
            )

        self.client = Github(self.token, per_page=100)

    def _rate_limit_sleep_seconds(self) -> int:
        """计算限流等待秒数"""
        try:
            rate = self.client.get_rate_limit().core
            return max(int(rate.reset.timestamp() - time.time()) + 1, 5)
        except Exception:
            return 60

    def _with_retry(self, operation: str, func: Callable[[], T]) -> T:
        """执行 API 调用，处理限流与短暂错误"""
        last_error: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                return func()
            except RateLimitExceededException as e:
                last_error = e
                if attempt >= self.max_retries:
                    break
                time.sleep(min(self._rate_limit_sleep_seconds(), 120))
            except GithubException as e:
                last_error = e
                retryable = e.status in {403, 502, 503, 504}
                message = (
                    e.data.get("message", str(e))
                    if isinstance(e.data, dict)
                    else str(e)
                )
                if not retryable or attempt >= self.max_retries:
                    raise GithubException(
                        e.status,
                        f"{operation}失败: {message}",
                    ) from e
                # secondary rate limit 等
                time.sleep(min(2 ** attempt, 30))
            except Exception as e:
                last_error = e
                if attempt >= self.max_retries:
                    raise
                time.sleep(min(2 ** attempt, 30))

        raise RuntimeError(f"{operation}失败（已重试 {self.max_retries} 次）: {last_error}")

    def get_latest_release(self, owner: str, repo: str):
        """获取仓库的最新Release"""
        def _fetch():
            repo_obj = self.client.get_repo(f"{owner}/{repo}")
            return repo_obj.get_latest_release()

        return self._with_retry(f"获取 {owner}/{repo} 的最新Release", _fetch)

    def get_ipa_assets(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """获取最新Release中的IPA文件"""
        latest_release = self.get_latest_release(owner, repo)
        return [
            {
                "name": asset.name,
                "url": asset.browser_download_url,
                "size": asset.size,
                "download_count": asset.download_count,
            }
            for asset in latest_release.get_assets()
            if asset.name.endswith(".ipa")
        ]

    def extract_release_info(self, owner: str, repo: str) -> Dict[str, Any]:
        """提取Release的关键信息"""
        release = self.get_latest_release(owner, repo)

        return {
            "tag_name": release.tag_name,
            "published_at": release.published_at,
            "body": release.body,
            "prerelease": release.prerelease,
            "draft": release.draft,
            "assets": [
                {
                    "name": asset.name,
                    "url": asset.browser_download_url,
                    "size": asset.size,
                }
                for asset in release.get_assets()
            ],
        }

    def validate_connection(self) -> bool:
        """验证GitHub连接"""
        try:
            self._with_retry("验证GitHub连接", lambda: self.client.get_user().login)
            return True
        except Exception:
            return False
