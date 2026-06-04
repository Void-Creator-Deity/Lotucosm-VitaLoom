"""
包签名校验：告警模式不阻断安装。
职责: 断言/回归上述契约。
时机: pytest 全量或单文件执行。
不变量: 不依赖人工 GUI；允许 mock SceneManager/PluginLoader。
排错: 失败见 docs/comment_standard.md 与同主题模块 README。

"""

import base64
import hashlib
import os
import tempfile
import unittest
import zipfile

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from builtin.editor_extensions.package_services import PackageOperationService


class _PM:
    def __init__(self, root):
        self.root = root
        self.cfg = {"disabled_plugins": [], "package_version_overrides": {}}

    def get_current_project_config(self):
        return dict(self.cfg)

    def update_project_config_fields(self, fields):
        self.cfg.update(fields)
        return True

    def get_current_project_path(self):
        return self.root


class TestPackageSignatureWarnOnly(unittest.TestCase):
    def _make_zip(self, td: str, name: str, content: bytes) -> str:
        zip_path = os.path.join(td, name)
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("payload.bin", content)
        return zip_path

    def _sha256(self, zip_path: str) -> tuple[str, bytes]:
        with open(zip_path, "rb") as f:
            raw = f.read()
        return hashlib.sha256(raw).hexdigest(), hashlib.sha256(raw).digest()

    def test_signature_invalid_warn_only(self):
        with tempfile.TemporaryDirectory() as td:
            zip_path = self._make_zip(td, "sig_invalid.zip", b"hello-signature")
            sha_hex, digest_bytes = self._sha256(zip_path)

            key_ok = Ed25519PrivateKey.generate()
            pub_ok = key_ok.public_key()

            key_sign = Ed25519PrivateKey.generate()
            sig_bytes = key_sign.sign(digest_bytes)  # sign with the "wrong" key

            signature_b64 = base64.b64encode(sig_bytes).decode("ascii")
            public_pem = pub_ok.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            ).decode("utf-8")

            pm = _PM(td)
            ops = PackageOperationService(pm)
            packages = [
                {
                    "id": "pkg.sig",
                    "version": "1.0.0",
                    "source": "file",
                    "dependencies": [],
                    "conflicts": [],
                    "artifact": {
                        "type": "file",
                        "path": zip_path,
                        "sha256": sha_hex,
                        "signature": signature_b64,
                        "public_key_pem": public_pem,
                    },
                }
            ]

            result = ops.install_package("pkg.sig", packages, enabled_ids=set(), mode="block")
            self.assertTrue(result.get("ok") is True)
            self.assertIn("signature_invalid", result.get("issues", []))

    def test_signature_unverifiable_warn_only(self):
        # repo 内置公钥文件不应存在（由实现回退分支决定）
        with tempfile.TemporaryDirectory() as td:
            zip_path = self._make_zip(td, "sig_unverifiable.zip", b"hello-unverifiable")
            sha_hex, digest_bytes = self._sha256(zip_path)

            key_sign = Ed25519PrivateKey.generate()
            sig_bytes = key_sign.sign(digest_bytes)
            signature_b64 = base64.b64encode(sig_bytes).decode("ascii")

            pm = _PM(td)
            ops = PackageOperationService(pm)
            packages = [
                {
                    "id": "pkg.sig2",
                    "version": "1.0.0",
                    "source": "file",
                    "dependencies": [],
                    "conflicts": [],
                    "artifact": {
                        "type": "file",
                        "path": zip_path,
                        "sha256": sha_hex,
                        "signature": signature_b64,
                        # 故意不提供 public_key_pem，触发签名不可验证分支
                    },
                }
            ]

            result = ops.install_package("pkg.sig2", packages, enabled_ids=set(), mode="block")
            self.assertTrue(result.get("ok") is True)
            self.assertIn("signature_unverifiable", result.get("issues", []))


if __name__ == "__main__":
    unittest.main()

