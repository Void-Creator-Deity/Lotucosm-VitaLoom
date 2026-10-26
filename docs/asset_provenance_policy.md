# 资产与图标来源策略

目标：仓库中的发布示范资产、UI 图标、工程贴图必须来源清楚。看不出来源的图片不能混进发行包。

## 原则

- UI 优先使用 Qt 标准图标、程序自绘图标、项目内自绘/生成资产。
- 不使用来源不明的网络图片、游戏截图、角色设定图、商用素材包图标。
- AI 生成或程序生成资产必须在 `assets/manifest.json` 记录生成方式和归属。
- 第三方资产只有在 license 明确、可再分发、并记录来源 URL/作者/许可证时才可进入发布包。

## 当前约束

示范工程 `workspace/projects/samples/*/assets/manifest.json` 必须包含 `sources` 字段。每个图片/音频资产都要有：

```json
{
  "origin": "project_generated",
  "generator": "tools/regenerate_sr_sprites.py",
  "license": "generated-project-owned"
}
```

允许的 `origin`：

- `project_generated`
- `generated_script`
- `project_drawn`
- `self_drawn`
- `qt_standard_icon`

允许的 `license`：

- `generated-project-owned`
- `project-owned`
- `self-owned`
- `qt-standard`

## 验收

```bash
python tools/check_asset_provenance.py
```

该检查会扫描示范工程发布资产；缺少 provenance 的图片/音频会失败。Hub 当前使用 Qt 标准图标，不需要把 Qt 图标复制进仓库。
