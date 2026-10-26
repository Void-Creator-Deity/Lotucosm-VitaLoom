# -*- coding: utf-8 -*-
"""Suite Hub product-version and capability overview dialog."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from hub.hub_runtime_info import build_runtime_summary
from hub.hub_paths import suite_root
from hub.project_list_model import discover_hub_projects


class HubInstallsDialog(QDialog):
    def __init__(self, repo_root: str, editor_version: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Product versions and capabilities")
        self.setMinimumSize(700, 500)
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        summary = build_runtime_summary()
        layout.addWidget(QLabel(f"Current product runtime: VitaLoom v{editor_version}"))
        install_label = QLabel(f"Application root: {summary['install_dir']}")
        install_label.setObjectName("vitaloomSubtle")
        layout.addWidget(install_label)
        plugin_label = QLabel(f"Official plugin files: {summary['plugin_file_count']}")
        plugin_label.setObjectName("vitaloomSubtle")
        layout.addWidget(plugin_label)

        tabs = QTabWidget()
        layout.addWidget(tabs, stretch=1)

        product_table = QTableWidget(0, 4)
        product_table.setHorizontalHeaderLabels(["Product", "Version", "Status", "Editor entry"])
        rows = []
        try:
            from FrameCore.product_registry import load_product_registry

            registry = load_product_registry(suite_root())
            for product_id, product in registry.products.items():
                for version in product.versions:
                    pv = registry.get_version(product_id, version)
                    rows.append(
                        (
                            product_id,
                            version,
                            "default" if version == product.default_version else "installed",
                            pv.entrypoints.get("editor", "") if pv else "",
                        )
                    )
        except Exception:
            rows = []
        product_table.setRowCount(len(rows))
        for row, (product_id, version, status, entry) in enumerate(rows):
            product_table.setItem(row, 0, QTableWidgetItem(product_id))
            product_table.setItem(row, 1, QTableWidgetItem(version))
            product_table.setItem(row, 2, QTableWidgetItem(status))
            product_table.setItem(row, 3, QTableWidgetItem(entry))
        _finish_table(product_table)
        tabs.addTab(_tab_page(product_table), "Versions")

        package_table = QTableWidget(0, 4)
        package_table.setHorizontalHeaderLabels(["Capability", "Name", "Version", "Plugins"])
        packages = summary["official_packages"]
        package_table.setRowCount(len(packages))
        for row, pkg in enumerate(packages):
            package_table.setItem(row, 0, QTableWidgetItem(pkg["id"]))
            package_table.setItem(row, 1, QTableWidgetItem(pkg["name"]))
            package_table.setItem(row, 2, QTableWidgetItem(pkg["version"]))
            package_table.setItem(row, 3, QTableWidgetItem(str(pkg["plugin_count"])))
        _finish_table(package_table)
        tabs.addTab(_tab_page(package_table), "Capabilities")

        project_table = QTableWidget(0, 3)
        project_table.setHorizontalHeaderLabels(["Project", "Version", "Path"])
        entries = discover_hub_projects(repo_root)
        project_table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            project_table.setItem(row, 0, QTableWidgetItem(entry.name))
            project_table.setItem(row, 1, QTableWidgetItem(entry.product_version or entry.loom_editor_version))
            project_table.setItem(row, 2, QTableWidgetItem(entry.path))
        _finish_table(project_table)
        tabs.addTab(_tab_page(project_table), "Projects")

        close_row = QHBoxLayout()
        close_row.addStretch()
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)  # type: ignore[arg-type]
        close_row.addWidget(close_button)
        layout.addLayout(close_row)


def _tab_page(table: QTableWidget) -> QWidget:
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(0, 8, 0, 0)
    layout.addWidget(table)
    return page


def _finish_table(table: QTableWidget) -> None:
    table.setAlternatingRowColors(False)
    table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.verticalHeader().setVisible(False)
    table.horizontalHeader().setStretchLastSection(True)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    table.resizeColumnsToContents()
