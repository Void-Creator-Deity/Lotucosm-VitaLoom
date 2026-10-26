# VitaLoom 重构方法复核与 E532 Replay/Topology Gate

日期：2026-10-12
状态：E532 阶段完成；全项目重构仍未完成。

## 目标与范围

复核旧长期重构路线是否仍适用于当前 FrameCore / versioned runtime 架构，并把 E531 动态 topology fresh-host provenance 纳入 E508 replay 证据拒绝矩阵。此 gate 只连接、校验和呈现证据，不创建 SR/PS 共同状态 owner，不执行 live replay，不改变 `.pond`、manifest、公共导入或环境管理。

本阶段修改范围：

- E508 replay corpus：一致性校验 producer 提供的 aggregate parity 与逐字段 parity / diff paths。
- E532 Qt-free runtime gate：校验 E508、E531 子证据，保留两个采集过程各自的 epoch 对，并显式保留不能证明的 binding 与 admission blockers。
- 定向测试和一个真实 GameViewport 证据检查工具。
- 本计划、`docs/mainline_status.md` 与文档索引。

不在范围：全仓目录重排、依赖环境迁移、自动改写旧计划、统一 SR/PS tick、native/OpenGL admission。Conda/uv 整理仍按用户此前要求暂缓。

## 路线复核结论

### 保留的决定

1. **FrameCore → 大插件 → versioned runtime → capability / extension → Project World** 分层仍清楚且与当前运行事实吻合；Qt-free contract 与 UI-host adapter 分离仍是正确约束。
2. **渐进迁移而非推倒重写**仍适用：每次改动保持旧 `.pond`、manifest、公共 API 和项目数据兼容；新的 authority 只在原 consumer 已切换且行为证据齐备后才替换旧路径。
3. **不把 parity、persistence 或签名当成 runtime authority**仍然正确。E508/E531 及本 gate 全部是只读证据；它们不能证明 live mutation、全状态 lossless 或 unified replay。

### 调整的工作方法

- 不再以“新增一个 receipt / audit 文件”本身作为架构进展。每个 gate 应绑定一条真实 producer → contract → consumer 路径，并确认错误、篡改、旧 epoch 和无副作用拒绝。
- 同一 lifecycle owner 尚未产生的证据不得靠相似字段或相同测试 fixture 拼成“端到端”证明。跨 artifact 组合必须显式记录 provenance；缺少共同 run / checkpoint / scene binding 时，结果只能是“不可 admission”。
- 优先修复证据内部可矛盾的状态，再做更高层组合。本阶段发现 E508 可接受 aggregate `parity=true`、但 `field_parity.sr_state=false` 且带有非空 diff path 的 corpus；新验证器在构造端与读取端都拒绝此矛盾，同时继续接受旧格式中没有逐字段字段的记录。
- 每个 gate 用可追溯事实报告：文件/接口边界、适用测试、真实宿主工具、通用门禁和未验证项；不使用测试总数、提交行数或模型 token 推算“整体重构百分比”。

## 公开资料及适用性

以下页面于 2026-10-12 在线核对。它们是方法参考，不覆盖 VitaLoom 自身 ADR 或产品兼容约束。

| 来源 | 对本项目有用的部分 | 不照搬的部分 |
|---|---|---|
| [Martin Fowler — Strangler Fig](https://martinfowler.com/bliki/StranglerFigApplication.html)（2024-08-22） | 通过逐段替换、保持系统可运行来控制大规模现代化风险；适合 runtime/adapter 的分步替换。 | 它不是要求每个内部模块都再建一层代理；已经稳定的 package seam 不应为了套模式而重复包装。 |
| [Martin Fowler — Branch by Abstraction](https://martinfowler.com/bliki/BranchByAbstraction.html)（2014-01-07） | 在稳定抽象后渐进迁移 implementation，保留旧实现作过渡并持续集成；适用于 Qt host、legacy editor command 等替换。 | 不把临时抽象长期保留成第二套 authority；切换完成后要有旧路径退役条件。 |
| [Microsoft Learn — Strangler Fig pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/strangler-fig) | 按功能切分并通过边界逐步迁移，提醒路由、观测和旧系统退出也属于计划。 | 该资料偏分布式/服务拆分；本仓不是微服务迁移，不引入网络路由或部署拓扑。 |
| [Microsoft Learn — Anti-Corruption Layer](https://learn.microsoft.com/en-us/azure/architecture/patterns/anti-corruption-layer) | 旧/新语义不一致时由明确 adapter 翻译，避免 legacy model 污染新的 domain contract；适用于 Qt adapter 和 legacy API compatibility。 | 不为同仓、同语义模块机械加 facade；translation 层必须有实际语义隔离收益。 |
| [Thoughtworks Technology Radar — Architectural fitness function](https://www.thoughtworks.com/radar/techniques/architectural-fitness-function) | 把关键架构约束做成持续运行的自动检查，而非仅靠文档审查；支持持续强化现有边界门禁。 | 不应把每项业务约束都变成脆弱的静态 grep；优先检查依赖方向和公开行为。 |
| [Pact — Introduction](https://docs.pact.io/) | contract test 应检查真实 consumer/provider 协议预期；支持针对插件、runtime 和 adapter 的双侧契约回归。 | 不因此引入 Pact 服务或网络级 consumer-driven contract infrastructure；当前范围是 Python 单仓接口测试。 |

## E532 设计与完成条件

1. E508 record 若携带 `field_parity`，必须有完整的六个被比较字段、严格布尔值，且 aggregate 与每字段事实一致。若携带 `field_diff_paths`，字段和值形状必须有效；aggregate parity 为真时不得有非空差异。旧 corpus 没有这些细项时仍可读取。
2. 新建 E532 gate 验证 E508 与 E531 各自的 schema/digest，记录 tick/event 数量和两套 runtime epoch；不能从“同一测试工具运行”推断它们来自同一个 host pair。
3. gate 永远报告 `host_capture_pair_binding_proven=false`、`topology_tick_binding_proven=false`、`checkpoint_scene_binding_proven=false`，并保持 `replay_admitted=false`、`default_ready=false`、`lossless=false`。
4. 真实 E532 checker 运行 E481/E531 与 E508 的真实 GameViewport 证据 producer，再生成诚实的拒绝矩阵；其通过只证明检查/拒绝路径工作，不代表 replay readiness。

### E532 完成记录（2026-10-12）

- E508 producer 与 consumer validator 均拒绝 aggregate/field parity 不一致；添加回归覆盖被重新计算 digest 的矛盾 artifact，证明校验不是只依赖 hash。
- 首次真实组合运行暴露 E508 portable projection 未排除 E527/E528 引入的 topology receipt `runtime_epoch` 与 `receipt_digest`，使 3 个 tick 的 SR state 都出现只限 host 的差异。将 projection 归属到 E508 Qt-free contract module；只去除 host identity，保留 topology generation 和 structure fingerprint。增加 fresh/source 双 host projection parity 与输入不变性回归。
- E532 Qt-free gate 校验并封装 E508 与 E531；逐项保留各自 epoch，不伪造 common-host 关联。拒绝矩阵明确 topology-to-tick、共同采集身份和 checkpoint/scene binding 均未证明。
- 新增真实检查工具，将 E481/E531 和 E508 的真实 GameViewport 输出送入 gate；工具结果必须报告三个 producer 通过，同时 gate 仍保持 replay/lossless/default-ready 为 false。
- 验证：E508/E509/E531/E512/E532 定向回归 `23 passed`；全量 `python -B -m pytest -q --basetemp=<unique-temp-dir>`：`2908 passed, 63 skipped, 64 subtests passed`；真实 offscreen `tools/check_worldbridge_e532_replay_topology_gate.py` 通过（E481/E531 与 E508 producers 有效，3 replay ticks、4 topology events）；双轨 comparability（50 ticks，seed 42，checkpoint 25/50）通过；core boundaries 与 release consistency 通过。
- 编译：改动 Python 源码逐文件 compile 检查通过、无尾随空格；全路径 compileall 命令返回成功，但因两个 workspace 临时目录访问受限输出 `Can't list ...` 警告，因此不能把该命令描述为完整 workspace 编译覆盖。
- 真实运行的 E508 source/fresh epochs 与 E531 source/fresh epochs 来自不同 viewport pair；gate 明确 `host_capture_pair_binding_proven=false`、`topology_tick_binding_proven=false`、`checkpoint_scene_binding_proven=false`，并保持 `replay_admitted=false`、`lossless=false`、`default_ready=false`。
- 该阶段完成不等于 E508/E531 同一批 host、checkpoint 或 `.pond` 的 provenance 已绑定；这是下一阶段需要改善的实际架构 seam，而非本 gate 可用 fixture 替代的事项。

### Exactly one next gate

**E533 — 让 topology 事件、tick、canonical input 与 RNG capture 共享同一 source/fresh host-pair identity，并由真实 GameViewport 生成可验证的 cross-artifact binding；缺少 checkpoint/scene 对照或任何 event-to-tick 对应时继续拒绝 replay。**

## E533 实施记录：同一 GameViewport pair 的 capture binding

E533 按上一 gate 的真实缺口推进，没有把 E508 和 E531 两次独立运行的相似
epoch 拼成端到端证明。新增 Qt-free `world_bridge_e533_capture_binding` contract
和真实 checker：source/fresh 两个 `GameViewport` 各自执行相同的三次 dynamic
spawn、一次 despawn；每个 topology event 都与同一次真实 tick 生成的 shared
envelope、canonical input event、RNG snapshot、live checkpoint 和 topology
receipt 放在同一 record 中。

contract 现在重新计算并校验：

- source/fresh host id、runtime epoch 和由 project/scene binding 派生的 pair id；
- topology event 的 kind、node set、structure fingerprint、receipt 和 checkpoint
  的交叉绑定；
- shared envelope 的 SR tick、sequence、capture epoch、canonical input sequence
  / digest、RNG context / snapshot digest；
- checkpoint 的 runtime epoch、scene、project lock digest、transport epoch，以及
  checkpoint RNG 与 envelope RNG 的一致性；
- source/fresh 的逻辑 tick offset、输入/RNG parity、拓扑结构 parity，以及 receipt
  / checkpoint 不跨 host 复用。

真实 checker 还对 topology tick 篡改和 fresh project/scene 错配执行拒绝检查。
因此 `host_capture_pair_binding_proven`、`topology_tick_binding_proven`、
`checkpoint_scene_binding_proven` 现在可以诚实地为 `true`；这仍然只是同一对
宿主的证据闭合，不等于统一 live mutation owner、lossless mapping 或 replay
authority，故 `replay_admitted`、`lossless`、`default_ready` 保持 `false`。

### E533 验证记录（2026-10-12）

- `python -B tools/check_worldbridge_e533_capture_binding.py` 通过：真实 pair、4
  个 topology event、每 tick 的 canonical input/RNG binding、project lock/scene
  digest binding、canonical round trip、tick tamper rejection 和 project mismatch
  rejection 全部通过。
- `python -B -m pytest -q tests/test_worldbridge_e533_capture_binding.py tests/test_worldbridge_e532_replay_topology_gate.py`：`6 passed`。
- 该阶段仍未改变默认 tick authority、live topology admission、lossless mapping
  或 native 状态；Conda/uv 环境整理按用户要求继续暂缓。

### Exactly one next gate

**E534 — 将 E533 的同宿主 capture record 接入统一 replay admission 的候选接口，
先证明跨 topology mutation 的 live owner、restore compensation 和全字段 mapping
均由同一个 authority seam 提供；任何字段缺失、owner drift 或失败补偿不闭合时
继续 fail-closed。**

## 验证与限制

验证命令和实际结果追加到 `docs/mainline_status.md`。真实 Qt smoke、全量 pytest、双轨 comparability 和 native build/parity 不因 E532 自动推定通过；未运行的项目必须继续列作未验证。
