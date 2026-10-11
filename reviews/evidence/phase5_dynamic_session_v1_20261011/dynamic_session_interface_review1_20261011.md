# 三周期动态 Session 接口只读审查 V1

Source READY SHA `5077b8d786e05616bfd6c5f69f6b86c9c7ee4c93ab9546d976db8ea78b7b443b` 与提供值匹配，30个列明文件的 bytes/SHA 全部匹配。只读取源码、清单与既有 canonical 数学实现；未编译、运行测试/优化/Model/native、修改 source/Git 或发送项目聊天消息。

## 必须修复：末轮 hint 可以越过声明的10s成功边界

`src/current_numeric_guess.hpp:19` 仅在轮次开头检查 elapsed≤10；LU、全行 violation 扫描及 stationarity 检查后，`:25` 直接设置 complete，`:28` 无新的 elapsed 检查。若最后一轮开始时尚未10s，但完成时已经越界，结果仍为 complete 并被 core `:937–944` 接受作 native seed。

建议最小修复：在 complete 发布前及返回成功前做 fresh elapsed gate，失败保留现有 events/primal/dual 并 complete=false；记录 actual hint whole-wall。这个修复会防止超时结果被当成完成的 hint，不能宣称阻止不可中断 LU 本身轻微越界；硬进程上限仍由新 native/pure profile 提供。本 finding 已发给 Root 内部审查聊天。

## 结构化接口结论

| 检查项 | 源码结论 | 位置 |
|---|---|---|
| 同一 Simulation / Session 三周期 | 两者仅在循环外创建；每周期新 observe、genuine nominal rollout、core Outcome、current-matrix hint/native workspace、独立 value rollout | active_first_cycle.cpp:45,50,70–102 |
| 当前边界 | Snapshot 私有 owner、最新 observation ID、完成 tick/sequence、实际仿真时间；validation和commit分别核验 integration exact bits | runtime_observer.cpp:115–134 |
| 一次 validation/token | validation_boundary 按实际完成 tick latch；重新 observe 同边界不能重新 mint；token私有Simulationowner，消费前必须 sessionActive/current 且未consumed | runtime_observer.cpp:123–136 |
| Commit历史与引用 | constructor 按≤8的有限 envelope reserve history；各 commit独立 outcome，不覆盖旧结果；既有 outcome引用在该有限范围内保持稳定 | runtime_observer.cpp:20–21,135；hpp:94–106 |
| 两真实2ms与发布 | exact token.C 写前/写后 durable events；两个 mj_step都必须通过原物理/独立scratch/完整geometry/sigma门；next counters和成功stage在acceptedhistory发布前，success最后赋值 | runtime_observer.cpp:137–160 |
| 部分失败 | attempted/returned/physicaltotal与已完成points留存；失败不发布acceptedhistory，failed_/inflight阻止后续current/observe/validation；两catch清除success | runtime_observer.cpp:145–160 |
| Shift范围 | 原160 controls按elapsed1做shift；仅填下一nominal controls，actual q/v/history来自下一真实观察，原state/maps/context/support/hint不shift | active_first_cycle.cpp:100–102 |
| 新求解绑定 | 在当前 connected 的 H/g/A/l/u/p/Z/scales上直接derive，不接受旧x/y；每周期fresh Outcome/单次solver latch/fresh backend owner=null；new API成功说明前置且catch resetrequest | integrated_horizon_qp.cpp:843–972 |
| 原安全门 | current hint不是candidate；仍需nativeSOLVED、原160重建、全部13156 SI、alpha严格.001、原rounded200history；B400与privateC仍必需 | integrated_horizon_qp.cpp:944–971；entry:89–100 |

## 非零 nominal / progress

`candidate_validation.cpp:19,22,26` 使用 genuine candidate−nominal 的 du8；初始 delta30=0，因为两条rollout共享真实initial。每个cell内 substep预测是 `state(m.state)+m.cell_A*delta_at_cell_start+m.cell_B*du`；仅在cell结束按原cellmap推进 delta。不是把candidate absolute controls错误地直接当perturbation，且 cell-cumulative映射不会误用前一个2ms delta。

`cycle_support.hpp::cellReference` 的 t=.004*zero_based_cycle+.002*half、cell-origin quadratic s/r，与 canonical `tools/phase5_public_coupled_augmented_cpp/public_coupled_augmented_model.cpp` 一致；B独立重现w/C、逐4ms s/r recurrence并bitwise检查原2msreference，包含finite/originalprogressdomains。非零 b/s/r的数学支持存在于helper和通用assessment；当前实际入口 `solveCurrentStabilizationInputTrust` 仍是 b_all0、起始s/r/previous_b0的诊断subset，不能声称已运行非零progress或完整任务。

## 初始证据与计时

- Assessment `:18` 从candidate actualInitial与当前Snapshot保存initial q/observation/transaction/time，查询完整true+cover，保存Local/body TCP Jacobian角行×.3及sigma，供first2ms区间界；entry `:96` 独立序列化validation_initial.bin。全部geometry witnesses仍在查询时核验，输出为声明的aggregate范围。
- inputs.posture_reference在每周期固定为循环外真实warmup后的before.q，未每次刷新目标。新nominal模型仍从当前cycle_before.actual q/v出发。
- CycleClock为每周期新实例，真实monotonic whole-wall覆盖观察到C+afterobserve+controls shift；SDK startup/termination、timing自身序列化及manifest明确排除。分段包含各自证据写入，Solve包含数值hint+native+其保留文件；CommitJournal分段结束后才afterobserve，whole-cycle仍包含它。失败时未完成的segment保持unavailable而非虚构0；whole-cycle retained并记录4ms miss，未因此制造在线claim。
- 当前face search≤512轮、faces≤n、KKT≤288维，输入n≤144/m≤20000；失败retain owned event prefix。完整10s结果门需按上文修复。

## 累计预算与失败语义

- 默认scope严格3commits/6forecasts/6tasksubsteps，Ledger在forecast/step尝试前预留；Simulation另有≤6真实taskstepattempts门、≤3成功commits门。physical warmup1000与task6明确区分。
- Ledger.sourceSlots只观察原Session BatchBudget单调累计，并未清零旧累计上限或制造新shared-ledger声明。源model/metadata驻留ticket在Session；每forecast/value各有独立CaseBudget/raw/source tickets，Session共享batch。token-own value在C完成前强持有raw生命周期；每周期forecast/core的旧支撑随owner正常释放。candidate SDK仅首次lazy启动核验，正常循环不重扫immutable dependencies。
- 每Evidence仍24artifacts/128MiB binary，三个独立cycle目录各受此门；Ledger统一768MiB binary/manifest预算，48MiB所有journals预算，各journal自身12MiB。BinaryFile写前预留、manifest写前预留；共用ledger不能通过new Evidence复位全局预算。当前每cycle约14个artifact，未达到24。新profile还须声明整个进程CPU/AS/wall/FSIZE限制，当前packet不是profile发布。
- Ledger.beforeForecast/beforeStep是保守的请求/预算预留计数：验证或journal append可能在实际Model/mj_step前失败。因此失败时 ledger.forecasts/steps不等于native进入事实；Simulation facts、value事实及solver forensics才是实际native调用证据。正常最终need(3/6/6)且每次成功要求各原门，不会由预留计数单独制造成功。
- 既有collector限制仍存在：journal receipt失败会跳过actual_commit.bin写入；failed_ Simulation拒绝cleanup observe，故依赖已保留journal/CommitOutcome/物理facts，不可宣称有失败后的完整Snapshot。若需要更完整失败证据，可独立best-effort序列化commitHistory，不能通过继续物理推进补齐。
- 成功返回前先通过三周期累计need、所有周期manifest、Session和Simulation termination及最终completion写入；任一标准异常使outer error非空。最终条件仍检查latest commit success/error为空；更直接检查ledger3/6/6可提升可读性，但当前已有前置need，无更少周期return0路径（显式termination_probe是另一路已声明测试hook）。

## 审查范围

Parent所述support tests PASS/compile PASS是既有事实，本审查没有重跑或独立核验Dell输出。此source只提供三周期offline诊断实现，geometryQP rows仍显式diagnosticempty，当前fullB几何门保留；没有D/E、停止/fulltask、实时/hardware或Phase5 acceptance结论。

## 随后收到的工作修复状态（非 V1 运行放行）

Root 报告：完整实际6351×126 guardedmatrix 的纯oracle在 V1 face search 第99次迭代以 dependent active-face KKT 拒绝，native0。因此 immutable V1 不放行，失败保留；本审查没有运行该oracle或独立读取其结果文件。

随后只读查看 working `/private/tmp/phase5_dynamic_session_active_v1_20261011/src/current_numeric_guess.hpp`：现为 feasible-start primal active-set，seed必须当前全行≤1e-12；direction KKT 使用当前gradient，逐非active行blockingfraction，direction近零时删除负乘子或检查最终全行/stationarity，完整event/partialx/y保留。其`:27` 发布complete前与`:38` 返回前 fresh within()，已解决上文时限结果门。基本法向符号、KKT方向和沿边界更新在源码中一致；负微小fraction归0仅限内部优化路径，最终仍要求全bounds，不更改candidate controls或原门。

这只是 working header 初步纯数学/接口阅读，不把改变算法的工作副本视作 immutable V1 修复，也不确认新算法在实际6351矩阵成功。新source packet/最终profile仍待另审，Parent称attempt18全fresh12TU编译中，本审查未核验该编译。

Phase5 NOT_ACCEPTED；Phase6 NOT_STARTED。旧冻结函数和旧失败证据保持；V1的重复事务接口结论与其数值hint失败应分别记录。
