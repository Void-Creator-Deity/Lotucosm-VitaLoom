# -*- coding: utf-8 -*-
"""Root Player launcher for the selected product version."""
from __future__ import annotations

import runpy
import sys

from main import _run_product_entry


def main() -> None:
    _run_product_entry("player", sys.argv[1:])


if __name__ == "__main__":
    main()
