# 工程目录（`projects/`）

| 子目录 | 用途 |
|--------|------|
| [`samples/`](samples/) | 内置示范工程（Hub 列表可见，可复制到 user） |
| [`user/`](user/) | 用户新建 / 导入的工程（Hub 默认保存位置） |

Hub 默认只扫描 `samples/` 和 `user/`。旧版平铺 `projects/*` 仅用于迁移兼容，
需要显式设置 `VITALOOM_INCLUDE_LEGACY_PROJECT_ROOTS=1` 后才会被发现。

## 示范工程（`workspace/projects/samples/`）

| 目录 | 用途 | 默认场景 |
|------|------|----------|
| [`pvaec-细胞演化/`](samples/pvaec-细胞演化/) | PVAEC 细胞演化 SR 演示 | `main_scene.pond` |
| [`pvaec-战争后进化/`](samples/pvaec-战争后进化/) | 三幕灾难演化（和平→战争→恢复） | `war_recovery_scene.pond` |
| [`织机教程-迷你Roguelike/`](samples/织机教程-迷你Roguelike/) | ScriptBase + 2D Roguelike 教学 | `dungeon_01.pond` |

打开方式：`python main.py` → Hub → 双击示范工程；或 **文件 → 打开项目**。

发行版用户也可直接浏览安装目录下的 `Samples/`（与 `workspace/projects/samples/` 相同）。

## 文档

- [pvaec-细胞演化/README.md](samples/pvaec-细胞演化/README.md)
- [pvaec-战争后进化/README.md](samples/pvaec-战争后进化/README.md)
- [织机教程-迷你Roguelike/README.md](samples/织机教程-迷你Roguelike/README.md)
