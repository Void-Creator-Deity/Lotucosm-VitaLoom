# PVAEC 生命阶段与认知发育 · 专项研究

> **文档性质**：面向 Lotucosm-VitaLoom / PVAEC 的研究综述与架构导向，综合生物学、比较认知科学与项目现有设计。  
> **不是**用户手册；工程操作见 [guides/README_PVAEC.md](guides/README_PVAEC.md)、[pvaec_cell_evolution.md](pvaec_cell_evolution.md)。  
> **撰写依据**：2026 年文献与项目代码对照；外部链接供深读，不保证第三方 URL 永久有效。

**目录**：§1 定位 · §2 认知四步 · §3–§4 生命阶梯 L0–L7 · §5–§7 学习/Barron/HRL · §8 代码映射 · §9–§11 Spec 与后续 · §14 收敛演化 · §15 Reafference · §16 HRL 形式对齐 · §17 关键期 · §18 Basal cognition · §19 空间认知 · §20 社会学习 · §21 Spec v0.2 · §22 开放问题 · §12/§23 参考文献 · 可比性见 [pvaec_comparability_research.md](pvaec_comparability_research.md)

---

## 1. 研究问题与项目定位

### 1.1 仓库要回答什么

本仓库名「基于继承算法实现的 AI 生命体」与 PVAEC（Perception–Verification Autonomous Evolution Cycle，感知–验证–自主演化循环）共同指向：

> **定义并实现一种数字生命如何在自身时间线里学习、验证、记忆与代际传递；莲池织机是承载这套法则的世界与工具，而不是目的本身。**

文档 [guides/README_PVAEC.md](guides/README_PVAEC.md) 中的哲学句：

- 摒弃「从静态数据学智能」；
- 生命在自身时间线里**验证行动是否改善内稳态**；
- PVAEC 是这一范式的可执行定义。

### 1.2 不是什么

| 常见误解 | 实际定位 |
|---|---|
| 生命模拟器 / 游戏引擎 | 织机 = 引擎；PVAEC = 研究语义；`workspace/projects/*` = 示范（见 [engine_competitive_landscape.md](engine_competitive_landscape.md)） |
| 具身智能产品 | 仅借鉴 EVAAA、Active Inference 等思路用于 verify/remember；见 README_PVAEC 免责声明 |
| 一次性 demo 脚本 | 示范工程 `pvaec-细胞演化` 是验证载体，不是 PVAEC 本体 |

### 1.3 本研究文档的范围

1. **系统发育（phylogeny）**：从单细胞到哺乳动物，神经系统如何演变、如何分区、各级职责是什么。  
2. **个体发育（ontogeny）**：生命体认识世界的顺序——先自我、再交互修正自我、再生态位、再意义世界。  
3. **与代码映射**：当前 runtime 实现了什么、缺什么、建议的 PVAEC 发育阶梯（Developmental Ladder）。

---

## 2. 核心认知顺序（项目愿景）

维护者与产品愿景可概括为四步（个体认识论顺序）：

```text
① 认识自己 — 熟悉自身能力（内感受、效应器、边界）
        ↓
② 与外界交互，再次认识自己 — 行动 → 验证 → 记忆（PVAEC 主轴）
        ↓
③ 认识自己在环境中的位置 — 邻居、生态位、关系结构
        ↓
④ 认识世界 — 规律、预测、Umwelt（对我有意义的世界，非上帝视角全图）
```

### 2.1 与 Piaget 个体发育的对照（类比，非等同）

| 步骤 | 发育心理学近似 | 生物学近似 |
|---|---|---|
| ① | 感觉运动期：用动作探索身体 | 内稳态、proprioception、Bauplan 限制的感知-效应器集 |
| ② | 因果性、物体恒常性 | habituation + verify：行动是否改善 essential variables |
| ③ | 前运算期：空间/他者参照（仍自我中心） | 生态位、群体密度、路径整合、reafference |
| ④ | 具体/形式运算：规则与抽象 | 层叠脑的跨时间预测与世界模型 |

**注意**：PVAEC 关注的是**生命体**的认识顺序，不是人类儿童心理学的精确复刻。

### 2.2 与 Uexküll 功能环的对照（强同构）

Jakob von Uexküll 的 **Funktionskreis（功能环）** 与上述四步结构一致：

```text
Bauplan（身体蓝图）→ 决定能感知/能作用什么
  Merkorgan → Merkzeichen（感知符号）
  Innenwelt（内部世界，内感受，唯一「直接可知」）
  整合 / 决策
  Werkorgan → Wirkzeichen（行动符号）
  改变 Umwelt（自我世界 ≠ 客观 Umgebung）
  reafference 内环：行动后果再感知
```

- **Umwelt** 是 Bauplan 的倒影：每个物种/live 的「世界」是主体 brought-forth 的意义域（生成论 / enactivism 延续此线）。  
- 现代 **sensorimotor**、**reafference**、**interoception** 均可在此框架下理解。

参考：[Internet Encyclopedia of Philosophy · Enactivism](https://iep.utm.edu/enactivism/) · [Uexküll 功能环 PDF 综述](https://cepa.info/fulltexts/2687.pdf)

---

## 3. 演变总逻辑：三条轴并行

比较认知演化研究（Barron et al. 2023；Ginsburg & Jablonka 2019）共识：

| 演变轴 | 驱动力 | 结果 |
|---|---|---|
| **身体轴** | 多细胞 → 细胞分工 → 胚层 → 器官 | 传感器/效应器物理分区 |
| **神经轴** | 协调压力 → 集中化 → 模块化 → 层叠 | 信息处理分区与控制流升级 |
| **学习轴** | 习惯化 → 联结 → 开放联结（UAL） | 可积累、可遗传的经验类型增加 |

**关键概念**：重大跃迁改变的是 **evolvability（什么认知能力可被演化出来）**，而非单纯「多加一个功能模块」。

---

## 4. 生命级别阶梯（L0–L7）

每一级列出：**演变转折 · 分区构成 · 各级职责 · 典型学习能力 · Barron 计算架构名**。

### Level 0 · 前神经 / 单细胞

**演变**：化学信号与胞内状态维持生存；无专门「脑」，已有 sensorimotor 闭环。

**分区构成**：

```text
细胞膜（边界 = 「我」）
  ├─ 受体（外感受）
  ├─ 胞内信号级联 / 表观遗传
  ├─ 效应器（鞭毛、纤毛、胞吐）
  └─ 胞内「记忆」（磷酸化、管腔几何、DNA 甲基化）
```

**职责**：

| 分区 | 职责 |
|---|---|
| 受体 | chemotaxis：营养/毒素梯度 |
| 内稳态回路 | ATP、渗透压、代谢 |
| 效应器 | 运动、摄食、排斥 |
| 胞内可塑性 | 习惯化；争议中的联结学习（草履虫 Gelber 实验，见 PMC7781593） |

**研究要点**：单细胞学习综述（*Learning in single cell organisms*）；黏菌 *Physarum* 无神经却有习惯化、迷宫、外化记忆（Quanta 2018）。

**对应认知四步**： mainly ① + ② 的雏形。

---

### Level 1 · 多细胞协作

**演变**：「时间分工的单细胞」→「空间分工的多细胞」；细胞类型分化可早于完整神经系统（Quanta 2019 关于 choanoflagellate/sponge 争议）。

**分区构成**：

```text
个体 / 群体
  ├─ germ（生殖系）
  ├─ soma（体细胞：营养、结构、防御）
  └─ ECM（细胞外基质，细胞间「公共空间」）
```

**职责**：分工与规模使协调成为瓶颈——为 Level 2 神经网铺垫。  
**参考**：*Understanding Multicellularity: The Functional Organization of the Intercellular Space* (PMC6759637)。

---

### Level 2 · 神经网期（刺胞动物）

**演变**：扩散协调不足 → **神经网**；近年发现海葵 *Nematostella* **口部神经环（ONR）** 等 ganglion-like 集群——**中枢化在两侧对称动物之前已开始**（bioRxiv 2026）。

**分区构成**：

```text
外胚层 — 皮肤 + 神经 + 感觉
中胶层 — 支撑
内胚层 — 消化
  └─ 神经网（贯穿，无单一中枢）
      ├─ 局部感觉-运动耦合
      ├─ 口部神经环（整合 hub）
      └─ pacemaker（节律运动）
```

**职责**：

| 分区 | 职责 |
|---|---|
| 局部神经网 | 刺激 → 局部收缩/运动 |
| 口部神经环 | 摄食协调、感觉-运动整合 |
| reafference | 区分自身运动所致刺激 vs 外源刺激（多细胞运动必需） |

**学习**：习惯化、敏感化、元素联结（刺胞动物部分有报告）。  
**Barron 架构**：**Decentralized（分散计算）** — 控制流 local、distributed。

---

### Level 3 · 集中神经节期（扁虫、线虫）

**演变**：两侧对称 + 主动捕食 → **centralization + cephalization**（头聚感官、头聚决策）。

**分区构成**：

```text
头节：cephalic ganglia + 前部感受器
神经索： longitudinal nerve cord
体节：节段神经节（节肢动物更明显）
```

**职责**：

| 分区 | 职责 |
|---|---|
| 头节神经节 | 统一决策、行为优先级、全身体协调 |
| 前部感觉 | 前进方向环境采样 |
| 神经索 | 命令下传 |

**学习**：多模态学习、泛化、情境学习、latent inhibition 等（线虫/扁虫实验）。  
**Barron 架构**：**Centralized（集中、前馈）** — master controller + feed-forward sensorimotor transform。

**对应认知四步**：③ 开始出现（头-尾、前后）。

---

### Level 4 · 模块化循环脑（昆虫）

**演变**：复杂导航与觅食 → **功能分区 + recurrent loops**。

**分区构成（昆虫经典模型）**：

```text
感觉层：Antennal Lobe（嗅） / Optic Lobe（视）
        ↓
学习与价态：Mushroom Body (MB)
  calyx → Kenyon cells → lobes → MBON
先天嗅觉：Lateral Horn
        ↓
导航与定向：Central Complex (CX) — 内部罗盘、目标方向、转向
        ↓
前运动 / 运动输出
```

**职责（研究中最清晰的分工范例）**：

| 分区 | 职责 |
|---|---|
| **Mushroom Body** | 联结学习、记忆、价态（valence）；coincidence detector |
| **MBON** | 记忆 → 趋/避行为 |
| **Lateral Horn** | 先天嗅觉反应（不经过学习） |
| **Central Complex** | 导航、heading、路径整合、「我在哪、朝哪走」 |
| **MB ↔ CX** | 经验调节导航目标 |

**Barron 架构**：**Recurrent（循环）** — reverberation、工作记忆、跨时间联结、选择性注意雏形。

**对应认知四步**：②③较完整；④ 仍为 route/snapshot 级，非抽象世界模型。

---

### Level 5 · 层叠脑（脊椎动物）

**演变**：更大身体、更长预测窗口 → **多个并行 recurrent 子系统层叠**。

**分区构成（现代模型，非「三脑洋葱」）**：

```text
脑干 — 生命维持、CPG 节律运动
边缘系统 — 内稳态驱力、动机、情绪标记
基底节 — action selection 门控（direct / indirect pathway）
小脑 — 动作精细校正、程序自动化
丘脑 — 各子系统 ↔ 皮层 的整合 hub
大脑皮层（六层）— 感觉 → 联合 → 前额叶（目标层级、规则、预测）
```

**职责**：

| 分区 | 职责 |
|---|---|
| 脑干 | 基本 reflex；去大脑皮层后仍可走跑但无目标导向（Sherrington 经典） |
| 下丘脑/边缘 | essential variables 驱力、episode 调节 |
| 基底节 | 从多个 cortical 计划中**选一个**执行 |
| 小脑 | 练习后程序迁移、误差校正 |
| 海马 | 空间/情境记忆 |
| 前额叶 | 层级目标、规则切换、后果预测 |

**重要修正**：MacLean「三脑理论（ reptilian → limbic → neocortex）」被现代神经科学视为**过度简化**；脑是**深度整合、并行演化改造**，非旧层被新层骑乘（Chin et al. 2022, *Psychological Review*）。

**Barron 架构**：**Laminated（层叠）** — 多时间尺度、预测、anticipation。

**Ginsburg & Jablonka**：此级别出现 **UAL（Unlimited Associative Learning）**——对复合刺激赋予动机值、开放-ended 目标行为；被视为 **minimal consciousness / sentience** 的演化标记（PMC5177968）。

---

### Level 6 · 反射 / 元认知（人类及近亲）

**演变**：前额叶扩展 → 系统可**访问并修改自身控制流**。

**职责**：规则推断、层级推理、符号/语言、mental selection（G&J 2025）；**reflection** — 程序读写自身控制架构。

**Barron 架构**：**Reflection**。

---

### Level 7 · 汇总表

| Level | 演变转折 | 核心分区 | 主要负责 |
|---|---|---|---|
| L0 单细胞 | 化学协调 | 膜/受体/效应器/胞内状态 | 内稳态 + chemotaxis + 习惯化 |
| L1 多细胞 | 空间分工 | germ / soma / ECM | 身体分工 |
| L2 神经网 | 扩散 → 网络 + hub | 神经网 / 胚层 / ONR | 协调 + reafference |
| L3 神经节 | 集中 + 头化 | 头节脑 / 神经索 | 统一决策 |
| L4 模块脑 | 前馈 → 循环 + 分区 | MB(学) / CX(位) | 记忆 vs 导航分工 |
| L5 层叠脑 | 单环 → 多 parallel 系统 | BG / 小脑 / 海马 / PFC | 选择、自动化、预测 |
| L6 反射脑 | 控制流自修改 | 前额叶 / meta | 规则、符号、元认知 |

---

## 5. 学习类型的演变（记什么、存在哪）

| 级别 | 学习类型 | 典型载体 | 「记忆」物理实现 |
|---|---|---|---|
| L0 | 习惯化 / 敏感化 | 细菌、黏菌、草履虫 | 胞内状态、管腔几何 |
| L2 | 元素联结 | 刺胞动物（部分） | 突触可塑性 |
| L3 | 多模态联结、泛化 | 扁虫、线虫 | 神经节网络 |
| L4 | 跨时间联结、工作记忆 | 昆虫 MB | Kenyon sparse code |
| L5 | 程序记忆、空间 episodic | 脊椎动物 | 海马 + BG + 小脑 loops |
| L5+ | **UAL** | 昆虫/脊椎/头足 | 中央关联 + 递归连接 |
| L6 | 符号、元认知 | 人类 | 前额叶 + 语言 |

**UAL 结构要求**（G&J）：感觉、运动、强化、记忆、评估单元的**双向递归连接**——这是架构跃迁，不是单模块参数 tweak。

---

## 6. Barron 五类计算架构（信息 flow 视角）

Barron, Halina & Klein (2023). *Transitions in cognitive evolution*. Proc. R. Soc. B 290: 20230671.

| 架构 | 代表生物 | 控制流特征 | 新 evolvable 能力 |
|---|---|---|---|
| Decentralized | 水螅 | 局部 distributed sensorimotor | 习惯化、敏感化、简单联结 |
| Centralized | 扁虫 | 前馈、头节 master controller | 多模态整合、泛化 |
| Recurrent | 昆虫 | 双向 recurrent loops | 工作记忆、跨时间联结、注意 |
| Laminated | 鸟类/哺乳 | 并行 interacting 子系统 | 多时间尺度预测、练习迁移 |
| Reflection | 人类 | 虚拟 control 修改 control flow | 符号、元认知、层级推理 |

可与形式自动机层次（HFA）对照建模（Macquarie University 后续工作）。

---

## 7. 内稳态与 EVAAA（验证信号从哪来）

PVAEC 的 **verify** 阶段与 EVAAA（Essential Variables in Autonomous and Adaptive Agents）平台一致方向：

- 用 **energy / health / hydration / temperature** 等 essential variables 作**内在验证**；
- **不是**外部手工 reward shaping；
- interoception 监控 internal state，reward 来自内稳态动力学（NeurIPS 2025 EVAAA；arXiv 2309.05999 interoception AI）。

项目实现：

- SR：`core/Lotucosm/sr_interoception.py` — `interoception_for_entity`、`homeostatic_success`
- PS：`PVAECCycle.validate_action` — energy/health 变化
- 脚本：`PvaecScript.verify` / `remember`（`homeostatic_pvaec_enabled`）

---

## 8. 与 Lotucosm-VitaLoom 代码映射

### 8.1 产品边界（复习）

| 模块 | 路径 | 职责 |
|---|---|---|
| Lotucosm | `runtime/core/Lotucosm/` | 宇宙、莲池、实体、PVAEC 脚本契约、SR tick |
| VitaLoom | `runtime/core/VitaLoom/` | 编辑器、视口、插件（非 tick 语义） |
| builtin | `runtime/builtin/` | Organism、InheritanceSystem、PVAECOrchestrator |
| 示范工程 | `workspace/projects/samples/pvaec-细胞演化/` | SR 脚本、场景、膜拓扑 |

### 8.2 PVAEC 双循环

| 循环 | 入口 | 职责 |
|---|---|---|
| **帧循环 · PVAEC 六步** | `PVAECCycle.run_cycle` / `PvaecScript.pvaec_step` | perceive → … → verify → remember（单体内） |
| **世代循环 · 编排器** | `PVAECOrchestrator.run_cycle` | 选择、繁殖、InheritanceSystem（整代） |

见 [experiment_guide.md](experiment_guide.md)。

### 8.3 发育阶梯 vs 当前实现

| Ladder Level | 应有能力 | 当前代码 | 缺口 |
|---|---|---|---|
| L0 Intero + explore | 仅内感受 + 随机 probe 效应器 | `interoception`；`generate_action` 的 explore | 无专门「能力图谱」阶段；出生即全参 |
| L1 Proprio / affordance | 熟悉 component/actuator | `components.sense/act` | 未分阶段解锁 |
| L2 Interaction verify | verify → remember | `PvaecScript`、`MemoryGene` | 验证偏标量，非自我模型 |
| L3 Ecological self | peers、niche、topology | `CentralBrainPvaec.perceive` | 数值有，无关系/角色表征 |
| L4 Phylogeny | 继承 + 突变 | `InheritanceSystem`、`sr_mind_gene` | SR/PS 繁殖语义未统一（ADR-0001） |
| L5 World model | 规律、预测 | ambient_field、bounds | 无长期世界模型 |
| L6 Meta | 改 learning 策略 | 无 | 未规划 |

### 8.4 示范脚本分工（L3–L4 混合 demo）

| 脚本 | 近似职责 |
|---|---|
| `sensor_patrol_pvaec.py` | 分布式 sense（膜 chemo） |
| `actuator_pulse_pvaec.py` | 分布式 act |
| `central_brain_pvaec.py` | 整合 + intero EMA + verify/remember |
| `evo_central_brain_pvaec.py` | + 代谢、繁殖、mind gene 突变 |

**问题**：`CentralBrainPvaec.perceive()` 一帧同时读内外全局状态——属**工程师全知感知**，非**生命发育顺序**。

### 8.5 建议的 PVAEC 模块分区（工程 target）

仿昆虫 MB / CX 职责分离：

```text
InteroModule          — L0：内稳态、自身状态
ProprioModule         — L0–1：component / actuator 能力图谱
SensorMesh            — L2：膜 receptor、分布式 sense
ActuatorMesh          — L2：分布式 act
MemoryBody (MB-analog)— L4：MemoryGene、价态、联结
NavigationBody (CX-analog) — L4：niche、heading、ecological position
CentralBrain          — L3–4：整合（现有 CentralBrainPvaec）
Evolution / Inheritance — phylogeny：InheritanceSystem、mind_dict_mutate
MetaController        — L6（远期）：attention / 学习率自修改
```

---

## 9. PVAEC 发育阶梯 Spec 草案（可评审）

供后续 ADR 或 `PvaecScript` 钩子扩展；**非当前实现承诺**。

### 9.1 两条轴

| 轴 | 含义 | 实现 knob 示例 |
|---|---|---|
| **Ontogeny** | 个体出生后认知展开 | `developmental_stage`、`age_ticks`、感知字段 unlock 表 |
| **Phylogeny** | 物种/架构复杂度 | 能力包、组件数、是否有 CentralBrain、是否可繁殖 |

### 9.2 Ontogeny 解锁表（草案）

| Stage | 名称 | 解锁感知 | 解锁行为 | 解锁记忆 |
|---|---|---|---|---|
| S0 | Neonate | intero only | random explore | 无 |
| S1 | Proprioceptive | + component echo | probe each actuator | 效应器-结果 pair |
| S2 | Interactive | + local sensor | chemotaxis loop | verify → remember |
| S3 | Social/Ecological | + peers, niche | 繁殖、膜拓扑 | MemoryGene |
| S4 | World | + field dynamics, bounds history | 预测性 movement | 长期规律 EMA |

**不变量**：`pause_on_complete: false` 的 SR 演示仍适用（见 [pvaec_cell_evolution.md](pvaec_cell_evolution.md)）——达标不暂停，符合「连续演化沙盒」。

### 9.3 Phylogeny 与继承

- 子代继承：`MemoryGene`、`MindProfile` 子集（`sr_mind_gene.GENE_KEYS`）、组件、膜边权。  
- **子代仍须从 S0–S1 重新验证**——遗传的是偏置与经验模式，不是全知世界地图。  
- 与仓库名「继承算法」一致：`InheritanceSystem` 负责 PS；SR 繁殖见 `evo_central_brain_pvaec.py`。

---

## 10. 设计原则（从研究提炼）

1. **级别升高 = 分区更专、职责更清晰**，不是单个 `perceive()` 读尽一切。  
2. **内稳态主轴**从 L0 存在；外部 reward 不是 PVAEC 本体。  
3. **Umwelt 边界**：每级只「认识」传感器可达、效应器可改、与 essential variables 相关的域。  
4. **循环连接**（L4+）才支撑跨时间学习与工作记忆。  
5. **非哺乳 ≠ 更笨**——黏菌用 geometry；昆虫用 Kenyon code；哺乳用层叠 cortex；**同一职责可不同实现**。  
6. **织机 ≠ PVAEC**；demo ≠ 终态；SR/PS tick 分离直至 unified 模式评审（[ADR-0001](adr/0001-dual-runtime-unification-seam.md)）。

---

## 11. 后续工作建议

| 优先级 | 项 | 产出 |
|---|---|---|
| P0 | 文档化 ontogeny unlock 为 ADR | `adr/0004-pvaec-developmental-ladder.md` ✅ |
| P1 | `PvaecScript` 增加 `developmental_stage` 与感知门控 | runtime API（见 §21）✅ 最小实现 |
| P1 | Memory / Navigation 模块职责拆分（MB/CX 类比） | 脚本 + builtin 边界 |
| P1 | Reafference 扩展 verify | `sr_interoception` + motor prediction | ✅ 三分 verify：homeo/reaff/exaff（SR） |
| P1 | PS ontogeny S0–S4 最小移植 | `ps_developmental.py` + `PVAECCycle` + 子代 S0 | ✅ 默认关；见 ADR-0004 §6 |
| P1 | PS verify 与 SR 三分对齐 | `ps_verify.py` + `use_verify_triple` | ✅ 默认关；ladder 开启时自动启用 |
| P2 | SR 繁殖与 PS `InheritanceSystem` 指标对齐 | EcologySnapshot 发育/verify 字段 | 见 [pvaec_comparability_research.md](pvaec_comparability_research.md) §3 |
| P2 | SocialMemoryModule 社会学习原型 | `social_memory.py` + `test_social_memory_smoke.py` | ✅ 最小 PS 轨 |
| P3 | Phase C.4 ADR 草稿 | `adr/0005-unified-pond-bridge.md` | ✅ 草案待评审 |
| P3 | NavigationBody cognitive map 最小实现 | 见 §19、§22 Q5 | ✅ place_code 熟悉度 + S3 解锁 |

---

## 12. 参考文献与链接

### 项目内

- [guides/README_PVAEC.md](guides/README_PVAEC.md)  
- [pvaec_cell_evolution.md](pvaec_cell_evolution.md)  
- [experiment_guide.md](experiment_guide.md)  
- [adr/0001-dual-runtime-unification-seam.md](adr/0001-dual-runtime-unification-seam.md)  
- [adr/0002-first-principles-and-layering.md](adr/0002-first-principles-and-layering.md)  
- [engine_competitive_landscape.md](engine_competitive_landscape.md)

### 外部（检索于 2026）

| 主题 | 来源 |
|---|---|
| 认知演化五架构 | Barron AB, Halina M, Klein C (2023). *Transitions in cognitive evolution*. Proc. R. Soc. B. [PubMed 37403503](https://pubmed.ncbi.nlm.nih.gov/37403503/) |
| 学习演化 transitions | Ginsburg S, Jablonka E (2019). *Evolutionary transitions in learning and cognition*. Phil. Trans. R. Soc. B 376:20190766. |
| UAL 与 minimal consciousness | Ginsburg S, Jablonka E. *The Transition to Minimal Consciousness through the Evolution of Associative Learning*. [PMC5177968](https://pmc.ncbi.nlm.nih.gov/articles/PMC5177968/) |
| 单细胞学习 | *Learning in single cell organisms*; *Reconsidering the evidence for learning in single cells* [PMC7781593](https://pmc.ncbi.nlm.nih.gov/articles/PMC7781593/) |
| 神经网 → 脑 | Richter & Rentzsch. *From nerve net to nerve ring, nerve cord and brain*. Nat Rev Neurosci. |
| 神经网区域化 | *Deep evolutionary roots of the nervous system*. Annu Rev Neurosci. |
| 海葵 ONR | *Morphological, molecular, and functional evidence for a CNS-like oral nerve ring*. bioRxiv 2026. |
| 昆虫 MB / CX | *What Do the Mushroom Bodies Do for the Insect Brain?* [PMC311238](https://pmc.ncbi.nlm.nih.gov/articles/PMC311238/) |
| 三脑论修正 | Chin et al. (2022). *Beyond Cortex: The Evolution of the Human Brain*. Psychol Rev. |
| Uexküll / 功能环 | [cepa.info Uexküll PDF](https://cepa.info/fulltexts/2687.pdf); [Enactivism IEP](https://iep.utm.edu/enactivism/) |
| EVAAA | Lee et al. (2025). *EVAAA: Essential Variables in Autonomous and Adaptive Agents*. NeurIPS. [GitHub cocoanlab/evaaa](https://github.com/cocoanlab/evaaa) |
| 黏菌学习与记忆 | Boisseau et al. (2016); Quanta *Slime Molds Remember* |
| 多细胞功能组织 | *Understanding Multicellularity* [PMC6759637](https://pmc.ncbi.nlm.nih.gov/articles/PMC6759637/) |

---

## 14. 收敛演化：三条独立「智能实验」谱系

认知能力在演化史上**多次独立出现**，硬件不同但**职责分区模式收敛**。对 PVAEC 的启示：同一发育阶段可用不同模块实现，只要**职责边界**一致。

### 14.1 昆虫谱系（L4 · Recurrent）

- **硬件**：MB（学习/价态）+ CX（导航/罗盘）+ AL/OL（感觉预处理）。  
- **特点**：脑小、循环连接、sparse coding。  
- **与 PVAEC**：最接近当前 `pvaec-细胞演化` 隐喻（膜 sensor/actuator + CentralBrain）。

### 14.2 脊椎动物谱系（L5 · Laminated）

- **硬件**：海马/内嗅皮层（cognitive map）+ 基底节（action selection）+ 小脑（程序自动化）+ 前额叶（层级目标）。  
- **特点**：并行子系统、多时间尺度。  
- **与 PVAEC**：PS 批实验 + `PVAECOrchestrator` 更接近「整代选择」；SR 缺层叠预测。

### 14.3 头足类谱系（独立 L4–L5 收敛）

- **背景**：与人类 LCA >5.6 亿年前；**独立演化**出大型神经系统（Godfrey-Smith；LSE Cephalopod Sentience）。  
- **硬件**：  
  - **垂直叶（vertical lobe）** — 学习回路，功能收敛于昆虫 MB / 哺乳海马（sparse input、联结记忆）。  
  - **分布式臂神经** — 臂具 autonomy，中央脑非唯一 CEO（类似 Brooks 分布式机器人；Octopus-inspired soft robotics）。  
- **能力**：空间学习、观察学习、**episodic-like memory**（墨鱼 remember what/where/when）；问题求解。  
- **与 PVAEC**：  
  - 支持「**无单一 CentralBrain 也可有学习**」的架构变体（分布式 PvaecScript + 局部 MemoryGene）。  
  - 支持「**同一职责、不同拓扑**」——不必复制昆虫 MB 结构。

### 14.4 收敛表（职责 → 多实现）

| 职责 | 昆虫 | 脊椎 | 头足类 | PVAEC 目标模块 |
|---|---|---|---|---|
| 联结/价态记忆 | Mushroom Body | 海马/皮层 | Vertical lobe | MemoryBody |
| 空间/导航 | Central Complex | 海马 place/grid | 未知（部分收敛） | NavigationBody |
| 先天反应 | Lateral Horn | 脑干 reflex | — | 硬连线 sensor→act |
| Action selection | MBON + CX | Basal ganglia | — | CentralBrain + BG-analog |
| 分布式执行 | 节段神经节 | 脊髓 CPG | 臂神经节 | ActuatorMesh |

参考：*Phylogenetic plasticity in the evolution of molluscan neural circuits* (Current Opinion Neurobiology)；*How intelligent is a cephalopod?* (Biological Reviews).

---

## 15. Reafference 与 body-self：「认识我」的演化基础

### 15.1 概念

| 术语 | 含义 |
|---|---|
| **Exafference** | 来自环境的刺激（静止动物唯一能感受的） |
| **Reafference** | 由**自身运动** inevitably 产生的感知 |
| **Efference copy** | 运动命令的副本，送入感觉通路 |
| **Corollary discharge (CD)** | 用 motor copy **抑制/补偿** self-generated 感觉 |

Jékely, Godfrey-Smith & Keijzer (2021) 主张：**早期神经系统大量 sensing 是 reafferent 的**；corollary discharge 是后来机制，但 **reafference 对 body-self 的起源至关重要**（[rstb.2019.0764](https://doi.org/10.1098/rstb.2019.0764)）。

### 15.2 与认知四步的对应

| 你的步骤 | Reafference 视角 |
|---|---|
| ① 认识自己 | proprioception + 内感受（Innenwelt） |
| ② 交互后再认识 | 行动 → reafference → 与 efference copy 比较 → 更新 self-model |
| ③ 环境位置 | 区分 self-motion vs external motion（否则无法导航） |
| ④ 认识世界 | 仅处理 **unpredicted** exafference（预测误差） |

**「不能给自己挠痒痒」**：efference copy 与感觉匹配 → 自我生成信号被 attenuate；不匹配 → 视为外部（von Holst & Mittelstaedt；PMC5153363）。

### 15.3 PVAEC 工程含义

当前 `verify()` 比较 act 前后 **intero**，尚未区分：

- self-generated 感知变化（预期内）  
- environment-induced 变化（预测误差）

**建议扩展**（Spec 级）：

```text
verify(obs_before, obs_after, action, efference_predicted_delta)
  → homeostatic_success(intero)
  → reafference_consistency(motor_out, sensed_delta)
  → unpredicted_exafference(obs_delta - predicted)
```

SR 已有 `sr_stress_norm`、`intrinsic_speed`；可逐步引入 **motor prediction buffer**（CentralBrain `act` 登记预期 Δ，下一帧 `perceive` 验证）。

---

## 16. 内稳态强化学习（HRL）与 PVAEC verify 的 formal 对齐

### 16.1 两套传统框架

| 框架 | 优化目标 | 典型应用 |
|---|---|---|
| **RL** | 最大化外部 reward | 游戏、任务 benchmark |
| **Homeostatic regulation (HR)** | 把 essential variables 维持在 setpoint | 生理稳态 |

Keramati & Gutkin (2011) 证明：在 drive-reduction 定义下，**最大化 discounted reward 等价于最小化 discounted drive**（[City University PDF](https://openaccess.city.ac.uk/id/eprint/20723/)）。

### 16.2 HRL 核心式（概念）

```text
drive(t) = || intero(t) - intero* ||     # 与 setpoint 偏差
reward_homeo(t) = f(drive_before) - f(drive_after)   # 内稳态改善 = 内在奖励
```

与 PVAEC `homeostatic_success(intero_before, intero_after)` **同构**。

### 16.3 与 IAI（Interoceptive Active Inference）并列

PMC8109616 对比：

- **HRL**：drive reduction → RPE → 更新 value → action selection  
- **IAI**：下行预测 desired internal state → 行动消除 prediction error  

PVAEC 当前更接近 **HRL 简化版**；若未来引入「期望内感受状态」，可向 IAI 靠拢——**仍非具身智能产品**，仅作 verify 数学参考。

### 16.4 EVAAA 课程与 ontogeny 平行

EVAAA 用 **环境难度递增 + essential variables 维持** 作 curriculum（NeurIPS 2025）。  
PVAEC ontogeny Stage S0→S4 可类比：

| EVAAA stage | PVAEC ontogeny |
|---|---|
| 简单环境、单 EV | S0–S1：仅 intero + explore |
| 多模态 sense + 捕食/资源 | S2–S3：sensor + verify |
| 未见测试床 generalization | S4：world model + 迁移 |

---

## 17. 个体发育关键期（Critical Period）与感知解锁

### 17.1 生物学

- **Critical period**：早期有限时间窗内，经验对回路形成**必需**；错过可不可逆（Hubel & Wiesel；V1 剥夺实验）。  
- **机制**：GABA 抑制回路成熟、perineuronal nets、silent synapse unsilencing/pruning。  
- **多感觉区**：S1/V1/A1 关键期**起始与峰值不同步**（PMC8970055）。  
- **不是单一窗口**：多种 plasticity burst 在不同脑区、不同时序（BrainFacts）。

### 17.2 对 PVAEC ontogeny 的启示

| 生物关键期 | PVAEC 类比 |
|---|---|
| 早期剥夺 → 永久缺陷 | Stage S1 未 explore actuator → 终生无 proprio map |
| 有序解锁（S1 早于 V1） | intero → proprio → extero → social → world |
| 关键期关闭后仍可有限 plasticity | 成年仍可 remember，但难「首次建立」新 modality |
| Cross-modal plasticity | 缺 peer 输入时 niche 通道被其他信号 repurposed |

**工程 knob**：`developmental_stage` + `stage_tick_budget`：每 stage 最少经历 N tick 的 verify 成功才 unlock 下一感知字段。

---

## 18. Basal cognition 与「自我边界」

### 18.1 Basal cognition 主张

Phil. Trans. R. Soc. B 376:20190750 *Reframing cognition*：

- 认知**不限于神经元**；单细胞 homeostasis、形态发生、再生规划均可作 **cognitive lens** 分析。  
- 工具：measurement, action, representation, goal, memory, decision —— 各组织层级均可问。

### 18.2 Computational boundary of a「Self」

Levin 等（Frontiers in Psychology 2019）：多细胞通过 **bioelectric / 信息共享** 扩大 **Center of Concern**：

- 单细胞：局部 micro-Umwelt  
- 组织：共享边界 → 更大 individual → 更大 goal state space  

与 PVAEC **从单组件脚本 → 膜拓扑有机体 → 种群** 的扩展同构。

### 18.3 Evolutionary Transitions in Individuality (ETI)

Smith & Szathmáry 式「重大转变」在个体性上：germ/soma 分工、抑制细胞自私、信息共享 —— Watson & Szathmáry 用 **deep learning / 非线性可分函数** 类比 ETI 所需关系结构。

**PVAEC 映射**：

| ETI | PVAEC |
|---|---|
| 单细胞 → 多细胞个体 | 单脚本 entity → 膜拓扑 multi-script organism |
| 个体 → 社会/colony | 单 organism → pond 种群 + niche |
| 遗传信息封装 | `MemoryGene` + `project.json` evolution_defaults |

---

## 19. 空间认知与 cognitive map（认识「位置」与「世界」）

### 19.1 Tolman cognitive map

Tolman (1948)：cognitive map 不限于迷宫空间——是**在行为相关维度上组织经验的系统**，支持 expectancies 与 planning（Eichenbaum & Cohen 2014 综述）。

### 19.2 海马 vs 昆虫 CX：收敛

| 系统 | 硬件 | 功能 |
|---|---|---|
| 哺乳 | 海马 place cells + 内嗅 grid cells | 空间 + **广义情境/ episodic** |
| 昆虫 | Central Complex + MB visual route | heading + snapshot / familiarity |
| 鱼/鸟 | 早期 place cells | 空间认知早于此前认为 |

**结论**：「认识环境位置」在演化上**多次收敛**；PVAEC 的 `niche_pressure`、`world_load`、`peers` 是 **CX-analog 输入**，但缺 **place code / cognitive map 数据结构**。

### 19.3 PVAEC NavigationBody Spec（草案）

```text
NavigationBody
  inputs:  position, heading, peers[], topology_edges, bounds
  state:    place_code_sparse | route_familiarity | niche_role
  outputs:  heading_suggestion, flee_vector, forage_bias
  learns:   snapshot familiarity (MB-analog 协作)
```

---

## 20. 社会学习与文化传递：遗传之外的第二种「继承」

### 20.1 与 InheritanceSystem 的区别

| 机制 | 时间尺度 | 传递内容 | 项目对应 |
|---|---|---|---|
| **基因/组件继承** | 代际 | 先天组件、MemoryGene、mind gene | `InheritanceSystem` |
| **社会学习** | 个体寿命内 / 群体代际 | 行为模式、路线、偏好 | ✅ `social_memory.py`（S3+，默认关） |
| **文化传递** | 多代 cohort | 传统、符号（bee dance） | **尚未建模** |

### 20.2 昆虫证据

- 蜜蜂 **waggle dance** — 符号化传递食物向量（local enhancement + 符号）。  
- **String pulling** — 蜜蜂观察学习 + 群体扩散（PLOS Biology 2017）；多代 learner→demonstrator 链。  
- **Nature 2024** — 熊蜂社会学习**个体无法独立创新**的复杂两步任务（ cumulative culture 雏形）。

### 20.3 PVAEC 扩展方向

在 **phylogeny L4+** 可引入：

```text
SocialMemoryModule
  observe(peer_id, action, outcome) → store as MemoryGene with social tag
  transmit: 子代 inherit 偏置 + 同 pond 邻居 act 可触发 copy-with-mutation
```

与「继承算法」互补：**基因继承**传倾向，**社会学习**传短期有效行为 —— 子代仍须 verify。

**Runtime（2026-06）**：`social_memory.py`（PS `memory_genes` + SR `sr_memory_genes`）；S3+ 且 `social_learning_enabled`；SR 经 `PvaecScript._maybe_record_social_peer`；props `"social": {"enabled": true}`。

---

## 21. 扩展发育阶梯 Spec v0.2

在 §9 基础上细化 **感知字段 unlock 表**（对接 `CentralBrainPvaec.perceive` 键名）。

| Stage | 解锁字段 | 关闭字段 | 最低 tick | 解锁条件 |
|---|---|---|---|---|
| S0 Neonate | `intero_*`（经 environment 注入） | peers, ambient, niche | 0 | 出生默认 |
| S1 Proprio | + `intrinsic_speed` | peers, world_load | 30 | ≥3 次 explore act |
| S2 Interactive | + chemo/sensor 局部 | niche, world_load_deriv | 100 | ≥5 次 verify success > 0.55 |
| S3 Ecological | + peers, niche, topology | — | 300 | 首次 remember 写入 |
| S4 World | + ambient_field, bounds history, world_load | — | 500 | 首次繁殖或 population>2 |

**PS 映射（2026-06 最小移植）**：组件 sense 键按 stage 过滤；`intero_*` 经 `enrich_ps_perception` 注入；进阶阈值复用 `can_advance_stage`。详见 ADR-0004 §6 与 `ps_developmental.py`。

**API 草案**（`PvaecScript`）：

```python
class PvaecScript(ScriptBase):
    developmental_stage: int = 0

    def perception_mask(self) -> frozenset[str]:
        """返回当前 stage 允许的 observation 键；宿主 perceive 后 filter。"""

    def on_stage_advance(self, new_stage: int) -> None:
        """解锁时回调；可重置 attention / 日志。"""
```

---

## 22. 开放问题与研究议程

| ID | 问题 | 可能路径 |
|---|---|---|
| Q1 | SR verify 是否应拆分 intero / reafference / exafference？ | ✅ `pvaec_verify_triple` + HUD `verify_*` |
| Q2 | 无 CentralBrain 的 distributed PVAEC 是否更「生命」？ | 头足类式：每组件 PvaecScript + 局部 MemoryGene |
| Q3 | ontogeny unlock 是否应写进 `project.json`？ | ✅ `developmental_profile` + ADR-0004（SR/PS） |
| Q4 | 社会学习 vs 基因继承如何共存？ | ✅ `social_memory.py`；子代仍须 verify |
| Q5 | cognitive map 最小实现？ | ✅ NavigationBody place_code + S3 解锁 |
| Q6 | UAL 级 architecture 需要何最小递归？ | 对照 G&J 五单元网络 vs 当前 flat MemoryGene |
| Q7 | critical period 关闭后 plasticity？ | ✅ `plasticity_window`：min_ticks 后放宽进阶条件 1 |
| Q8 | PS verify 是否与 SR 共用三分？ | ✅ `ps_verify.validate_action_triple` |
| Q9 | EcologySnapshot 发育/verify 跨轨字段？ | 同上 §3 |
| Q10 | Phase C.4 unified_pond 何时立项？ | 同上 §4；依赖 Q8 部分落地 |

---

## 23. 参考文献与链接（续）

| 主题 | 来源 |
|---|---|
| Reafference / body-self | Jékely et al. (2021). *Reafference and the origin of the self*. [rstb.2019.0764](https://doi.org/10.1098/rstb.2019.0764) |
| Corollary discharge | *Corollary discharge across the animal kingdom*. [PMC5153363](https://pmc.ncbi.nlm.nih.gov/articles/PMC5153363/) |
| HRL 理论 | Keramati & Gutkin (2011). *A Reinforcement Learning Theory for Homeostatic Regulation* |
| HRL 综述 | *Computational Models of Interoception and Body Regulation*. [PMC8109616](https://pmc.ncbi.nlm.nih.gov/articles/PMC8109616/) |
| CTCS-HRRL | arXiv:2401.08999 |
| Critical periods | PMC8970055；BrainFacts *Critical Periods* |
| Basal cognition | *Reframing cognition*. [rstb.20190750](https://doi.org/10.1098/rstb.20190750) |
| Self boundary | Levin et al. (2019). *Computational Boundary of a Self*. Frontiers in Psychology |
| Cognitive map | Eichenbaum (2014)；*Memory and Space* J Neurosci 2015 |
| 头足类智能 | Godfrey-Smith；LSE *Cephalopod Cognition and Sentience* |
| 头足类 learning circuit | *Phylogenetic plasticity in molluscan neural circuits* |
| 昆虫社会学习 | PMC5544272；Nature 2024 bumblebee puzzle box |
| Mental selection | Ginsburg & Jablonka (2025). *Consciousness: its goals…* [rstb.2024.0310](https://doi.org/10.1098/rstb.2024.0310) |
| ETI / deep learning analogy | Watson & Szathmáry；Frontiers in Ecology and Evolution 2022 |

---

## 24. 文档维护

- **版本**：v1.3（2026-06-12）— PS ontogeny 落地；新增可比性专项 [pvaec_comparability_research.md](pvaec_comparability_research.md)（Q8–Q11）。  
- **上一版**：v1.2 — ADR-0004、runtime `developmental_stage`/`perception_mask`、遗传对齐文档。  
- **更新时机**：PS verify 三分、EcologySnapshot 发育字段、Phase C.4 ADR 评审后修订 §11、§22。  
- **维护者**：架构 / PVAEC 语义负责人。
