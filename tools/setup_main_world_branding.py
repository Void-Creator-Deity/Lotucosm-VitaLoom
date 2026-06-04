#!/usr/bin/env python3
"""将 PVAEC · 细胞演化 工程 PNG 复制为工程内 branding/logo.png（非引擎启动画面）。"""

from __future__ import annotations

import shutil
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    assets = root / "projects" / "pvaec-细胞演化" / "assets"
    src = assets / "未标题-1.png"
    branding = assets / "branding"
    branding.mkdir(parents=True, exist_ok=True)
    dst = branding / "logo.png"
    if not src.is_file():
        print("skip: source not found", src)
        return
    shutil.copy2(src, dst)
    print("Wrote", dst)


if __name__ == "__main__":
    main()
