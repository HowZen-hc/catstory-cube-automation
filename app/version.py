"""版本管理與更新檢查。"""

import json
import logging
import urllib.request

logger = logging.getLogger(__name__)

__version__ = "0.4.0"

_GITHUB_REPO = "HowZen-hc/catstory-cube-automation"
RELEASE_API_URL = f"https://api.github.com/repos/{_GITHUB_REPO}/releases/latest"
RELEASE_PAGE_URL = f"https://github.com/{_GITHUB_REPO}/releases/latest"


def _parse_version(v: str) -> tuple[int, ...]:
    """將版本字串轉為可比較的 tuple，例如 '0.3.1' → (0, 3, 1)。

    容許 pre-release 後綴（如 '1.2.3-beta'），僅取數字部分。
    """
    # 取 '-' 或 '+' 之前的部分（去掉 pre-release / build metadata）
    base = v.strip().split("-")[0].split("+")[0]
    return tuple(int(x) for x in base.split("."))


def check_for_update() -> tuple[bool, str]:
    """檢查 GitHub 是否有更新的 release。

    Returns
    -------
    (has_update, latest_version)
        has_update: True 表示有新版本
        latest_version: 最新版本號（不含 v prefix）

    Raises
    ------
    Exception
        網路錯誤或 API 回應格式異常時拋出。
    """
    req = urllib.request.Request(
        RELEASE_API_URL,
        headers={"Accept": "application/vnd.github.v3+json", "User-Agent": "CubeAutomation"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())

    latest = data["tag_name"].lstrip("v")
    has_update = _parse_version(latest) > _parse_version(__version__)
    return has_update, latest
