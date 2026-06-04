"""下载器基础设施插件：通用 HTTP 下载并注册 EditorContext.services。

排错: 见 `builtin/README.md`。
"""

from __future__ import annotations

import json
import os
import hashlib
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from core.plugin.interfaces import IEditorPlugin


@dataclass
class DownloadResult:
    """HTTP 下载结果：成功时带 bytes，失败时带 error 与可选 status。"""

    ok: bool
    data: Optional[bytes] = None
    error: Optional[str] = None
    status: Optional[int] = None


class DownloaderService:
    """通用下载服务：bytes 下载、json 下载、sha256 校验（可选）。"""

    def __init__(self, cache_dir: str):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def fetch_bytes(
        self,
        url: str,
        timeout_s: int = 8,
        cache_key: Optional[str] = None,
        expected_sha256: Optional[str] = None,
    ) -> DownloadResult:
        try:
            if cache_key:
                cached_path = os.path.join(self.cache_dir, cache_key)
                if os.path.exists(cached_path):
                    with open(cached_path, "rb") as f:
                        data = f.read()
                    if expected_sha256 and not self._verify_sha256(data, expected_sha256):
                        return DownloadResult(ok=False, error="sha256_mismatch(cached)")
                    return DownloadResult(ok=True, data=data)

            with urllib.request.urlopen(url, timeout=timeout_s) as resp:  # nosec - URL comes from registry config
                status = getattr(resp, "status", None)
                data = resp.read()

            if expected_sha256 and not self._verify_sha256(data, expected_sha256):
                return DownloadResult(ok=False, data=None, error="sha256_mismatch", status=status)

            if cache_key:
                cached_path = os.path.join(self.cache_dir, cache_key)
                with open(cached_path, "wb") as f:
                    f.write(data)

            return DownloadResult(ok=True, data=data, status=status)
        except Exception as e:
            return DownloadResult(ok=False, error=str(e))

    def fetch_json(self, url: str, timeout_s: int = 8) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        res = self.fetch_bytes(url, timeout_s=timeout_s)
        if not res.ok or res.data is None:
            return None, res.error or "download_failed"
        try:
            text = res.data.decode("utf-8", errors="replace")
            return json.loads(text), None
        except Exception as e:
            return None, str(e)

    @staticmethod
    def _verify_sha256(data: bytes, expected_hex: str) -> bool:
        expected_hex = expected_hex.strip().lower()
        actual = hashlib.sha256(data).hexdigest().lower()
        return actual == expected_hex


class DownloaderPlugin(IEditorPlugin):
    """注册 DownloaderService 到 editor_context.services；卸载时移除服务。"""

    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "Downloader",
            "version": "1.0.0",
            "author": "VitaLoom Team",
            "description": "官方下载服务（供包管理器/官方插件复用）",
            "dependencies": [],
            "provides": [],
            "protected": True,
        }

    def on_load(self, editor_context):
        self.context = editor_context
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        cache_dir = os.path.join(repo_root, "data", "system", "download_cache")
        self.service = DownloaderService(cache_dir=cache_dir)

        services = getattr(self.context, "services", None)
        if services and hasattr(services, "register"):
            services.register("downloader", self.service)

    def on_unload(self):
        try:
            services = getattr(self.context, "services", None)
            if services and hasattr(services, "unregister"):
                services.unregister("downloader")
        except Exception:
            pass

    def on_editor_ready(self):
        return

