"""版本管理相關測試。"""

import re
from pathlib import Path
from unittest.mock import patch

import pytest

from app.version import RELEASE_PAGE_URL, _parse_version, __version__, check_for_update


class TestVersionSync:
    """確保 app/version.py 與 pyproject.toml 的版本號一致。"""

    def test_version_matches_pyproject(self):
        pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
        match = re.search(r'^version\s*=\s*"(.+?)"', pyproject, re.MULTILINE)
        assert match is not None, "pyproject.toml 中找不到 version 欄位"
        assert match.group(1) == __version__


class TestParseVersion:
    def test_simple(self):
        assert _parse_version("0.3.0") == (0, 3, 0)

    def test_major(self):
        assert _parse_version("1.0.0") == (1, 0, 0)

    def test_with_whitespace(self):
        assert _parse_version(" 1.2.3 ") == (1, 2, 3)

    def test_comparison(self):
        assert _parse_version("0.3.1") > _parse_version("0.3.0")
        assert _parse_version("0.4.0") > _parse_version("0.3.9")
        assert _parse_version("1.0.0") > _parse_version("0.99.99")
        assert _parse_version("0.3.0") == _parse_version("0.3.0")

    def test_prerelease_suffix_stripped(self):
        assert _parse_version("1.2.3-beta") == (1, 2, 3)
        assert _parse_version("1.0.0-rc.1") == (1, 0, 0)
        assert _parse_version("2.0.0+build.123") == (2, 0, 0)


class TestCheckForUpdate:
    def _mock_response(self, tag_name: str):
        """建立模擬的 GitHub API response。"""
        import io
        import json

        body = json.dumps({"tag_name": tag_name}).encode()
        resp = io.BytesIO(body)
        resp.__enter__ = lambda s: s
        resp.__exit__ = lambda s, *a: None
        return resp

    def test_has_update(self):
        with patch("app.version.urllib.request.urlopen") as mock_open:
            mock_open.return_value = self._mock_response("v99.0.0")
            has_update, latest = check_for_update()
        assert has_update is True
        assert latest == "99.0.0"

    def test_no_update(self):
        with patch("app.version.urllib.request.urlopen") as mock_open:
            mock_open.return_value = self._mock_response(f"v{__version__}")
            has_update, latest = check_for_update()
        assert has_update is False
        assert latest == __version__

    def test_older_remote(self):
        with patch("app.version.urllib.request.urlopen") as mock_open:
            mock_open.return_value = self._mock_response("v0.0.1")
            has_update, latest = check_for_update()
        assert has_update is False

    def test_network_error(self):
        with patch("app.version.urllib.request.urlopen") as mock_open:
            mock_open.side_effect = OSError("timeout")
            with pytest.raises(OSError):
                check_for_update()

    def test_prerelease_tag(self):
        with patch("app.version.urllib.request.urlopen") as mock_open:
            mock_open.return_value = self._mock_response("v1.0.0-beta")
            has_update, latest = check_for_update()
        assert has_update is True
        assert latest == "1.0.0-beta"

    def test_missing_tag_name(self):
        import io
        import json

        body = json.dumps({"name": "Release v1.0"}).encode()
        resp = io.BytesIO(body)
        resp.__enter__ = lambda s: s
        resp.__exit__ = lambda s, *a: None
        with patch("app.version.urllib.request.urlopen") as mock_open:
            mock_open.return_value = resp
            with pytest.raises(KeyError):
                check_for_update()

    def test_release_page_url_format(self):
        assert "HowZen-hc/catstory-cube-automation" in RELEASE_PAGE_URL
