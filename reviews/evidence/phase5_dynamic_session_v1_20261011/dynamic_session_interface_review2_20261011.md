# 三周期动态 Session 接口差异审查 V2

结论：只审 V1→V2 实际差异，未发现新增必须修复问题。V1时限 finding 与普通journal receipt失败跳过commit细节的问题已修复。未编译/执行纯oracle、Model或native，未改source/Git，未发项目聊天消息。

READY SHA `bf27985f7f2ac9d4d5626e596de9ee47f453fda9f575d581053455a19ccca12e` 与提供值一致，31个列明文件 bytes/SHA 全部匹配，prior_READY指向已审V1。源码变化仅 current_numeric_guess.hpp、integrated_horizon_qp.hpp/cpp、cycle_support.hpp/tests、active_first_cycle.cpp；runtime/token/两真实子步/acceptedhistory/Session原budget/B数学等文件均原字节。另有design更新与V1历史报告。

## Hint 与时限

- `current_numeric_guess.hpp:17–20` 在入口开始计时，输入完整finite/shape核验也计入10s；使用传入current solver_seed，必须对全部当前bounds≤1e-12。没有 projection 或旧solution reuse。
- 方向KKT使用 `-(H*x+g)` 和 active面齐次方向，upper normal=+A / lower normal=−A；非active行按blocking fraction推进。direction近零时删除显著负lambda或检查所有当前primal/stationarity；每一步全bounds≤1e-12。内部极小负fraction归0只影响数学优化路径，不能直接clip candidate controls。
- `:27` 先final scan/stationarity再within()再complete；`:38` 返回前再within()，若超时catch complete=false并保留events/x/y。修复的是超时结果不能发布成功；不可中断LU的硬时限仍依赖进程profile。
- core `:938` 对当周期实际H/g/A/l/u调用derive并传transform.solver_seed；结果finite/shape核验后仅作fresh native primal/dualguess。原OSQP options、nativeSOLVED、fulloriginal SI、strict、B/C门均未改。

## Separate cumulative numeric 48M

- Inputs新增reserve_separate_numeric callback，frontend绑定循环外同一Ledger，整个current Outcome使用期间ledger仍活着。
- inline `:124–127` 在H/g/A/F等持有数组分配前预留实际planned slots；current solver `:862` 在screen/reduction分配前预留4M，`:937` 在hint/KKT分配前预留2M。callback失败则原异常路径拒绝，不进入native。
- Ledger.reserveNumeric按cap−spent检查并checkedAdd，累计永不退还或清零；default48,000,000。当前geometryempty固定qrows13156、factor741的inline plan为2,459,213，因此成功三周期预留总数25,377,639，低于48M。这是逻辑数组累计预算，不是RSS/allocator/native/temp总内存。
- 原Session BatchBudget/CaseBudget代码原字节，不通过独立数值ledger扩展旧1.024B累计上限。binary768MiB/journal48MiB全局预算及各Evidence/journal上限也未改变。
- tests新增numeric cap拒绝与计数保留断言，本审查未运行测试。

## Commit evidence 失败保存

- `emitCommitRecord` 的字段顺序与V1 actual_commit.bin原writer body字节级一致：attempted/success/nativeattempts/returns、stage/error、四个history counters、heldC/time、pointcount、每point原字段。actual_commit V1角色可继续使用。
- entry `:99–101` 单独捕获普通receipt异常，随后先写actual_commit，再以receipt原错误停止循环；receipt失败不再直接跳过commit writer。若错误字符串自身分配失败/非标准异常或OS写失败，写入仍可能不完整，最终backup是best-effort，未承诺硬中断完整文件。
- `:113` 父Evidence在cleanup observe之前独立写retained_commit_history.bin；无需current()/observe()，可在Simulation.failed_为true时读取私有owned历史。序列化先history count，再重复同一emitCommitRecord，最后scope说明，保留所有成功与部分失败记录。未将失败后的物理state伪装成acceptedhistory。
- callback及serialization只读owned outcomes，无二次物理步或target写；该artifact失败也会保留outer error并继续独立termination尝试。字段/role可区分单条与完整history，无无界读取/计数问题。
- 父目录增加一个artifact，当前正常路径仍远低于24句柄/128MiB上限；父/子所有写入继续统一Ledger预留。

## 格式提示（非执行阻断）

cycle_timing.bin在四个旧累计u64后新增separateNumericSlots第五个计数，role仍为原unversioned `ACTUAL_OFFLINE_CYCLE_SEGMENTS_AND_4MS_MISS`。当前没有发现仓库内已有读取器，source READY明确给出V2 writer，因此本次不把它作为运行阻断；未来读取器必须按V2布局读取5计数，不能按V1读4计数后把第五个计数当text长度。建议后续使用V2角色或显式计数字段数，避免只按role解析造成歧义。

新版Event.worst_row在fraction路径实际表示blocking row，终止/删面事件可能−1；不要解读为每轮全行最大violation的原SI索引。仍是hint内部scaled roster诊断，非candidate违规索引。

## 证据边界

Parent报告：旧实际6351×126矩阵的pure18新算法PASS147events/0.383s，NumPy stationarity1.7347e−18 / violation4.3368e−19 / alpha.000999；这支持该已归档矩阵上的纯数学hint，不证明下一真实current矩阵或三周期Model/B/C成功。本次未索取或独立读取Dell结果，因此这些数值为Parent提供事实，不是本审查实测。

Parent称19全fresh12TU compilePASS/native0，20仅entry保留修复freshcompile中；本报告只确认immutable源差异，未确认最终ELF/profile或给出native执行发布。Phase5 NOT_ACCEPTED；Phase6 NOT_STARTED。
