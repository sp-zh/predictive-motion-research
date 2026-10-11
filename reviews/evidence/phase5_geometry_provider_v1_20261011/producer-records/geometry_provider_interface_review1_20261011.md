# Recorded nominal geometry provider 接口审查

结论：本轮发现的三处问题已由 Root 修复，当前工作源复读确认；其余计数、选择、取样/EOF、输出与调用范围未发现新增阻断。只读源码与封存二进制，未编译、执行provider/优化/Model/native、修改source/Git或发送项目聊天消息。

## Finding 与修复状态

1. 初读 `counted_geometry.hpp` 的局部 `Pose pose` 遮蔽成员pose，initializer内未限定调用无法编译。现`:17` 使用 `this->pose`；Parent报告attempt23同一compile错误保留/native0。
2. `provider_probe.cpp:38` point FD/J residual直接std::max可能吞掉NaN。现materialize `point_residual`，检查fd/J/residual finite后才max；CountedScene FK/J wrapper也加入finite返回检查，原1e−7/1e−5/1e−4阈值未改。
3. 初读completion字符串在write/fsync失败前预先包含success=1，catch后stdout仍打印旧字符串。现`:51` report lambda读取最终error重新构造，stdout补completion_written。失败不能以旧stdout success掩盖非零exit；文件写失败仍保留其实际prefix。

当前读取文件身份（工作源会继续变化，非immutable READY）：

- counted_geometry.hpp SHA `180ea5a855dfac54d1a1cc6476a0a024623bce67143820624660e09cbadb1fcb`
- provider_probe.cpp SHA `6f4b49e67d92b667dc3b2ca52c4403f81453b5d11d98af2a78e7e09cbebc1091`
- nominal_geometry_selection.hpp SHA `6a41cc80feca43509d234c5aaf70e9a4c4de77abfa9b8eabfec6b6541b7711fa`
- upstream_geometry.hpp SHA `65150b6e7d1b83cb0e3ec81fd2f6331216e6bfa19460aa329335c96fd1cb2e00`

## 原数学与计数

upstream_geometry.hpp 与 canonical `tools/phase4_adapters/geometry.hpp` 整体字节相同。CountedScene query复制其原placements/exclusions、Coal signed distance与GJK/EPA1e−10/256设置、true gradient pointJacobian和cover box/floor/sphere数学。新增只包括计数插入、FK/J wrappers及finite加强；未发现Eigen悬空表达式：pointJacobian返回拥有MatrixXd，probe J完整拥有；fd为固定Vector3d，query所有gradient赋值在表达式临时存活期间完成。

单个Counts对象在整个main共享：Scene进入前1400门；Coal true或analytic cover primitive前20M门；非world FK与flange/probe FK前40000门；analytic J前20000门；returned值与scene_returns只在各指定正常返回路径更新。固定1200base queries，9个固定样本各±7 joints为126扰动queries，总1326<1400，9035完整roster意味着成功scope primitive总11,980,410<20M。失败立即停止主循环，不retry，不因Scene新实例复位计数。

所有实际probe calls静态类型是CountedScene，其pose/jac/query包装覆盖调用；未发现走Scene::query绕计数的实际路径。公开继承本身不是抗恶意base-cast接口，计数也不是Pinocchio内部缓存/深层FK调用全量统计；它记录这里声明的Scene/primitive/framePose/frameJacobian API范围。

## Selected rows / 梯度诊断

- 每个完整roster检验9035条query的finite距离、gradient7、world witness/unit normal/一致性。identity包含type/a/b/cover_index，selection保证唯一/有界且最低true/cover与snapshot minima一致。
- deterministic距离排序+identity tie break，取2true+2cover；每个400sample产生1600行，3周期总4800。row.Jq为原Query.gradient，nominal_value原distance，lower=.005m/upper1e6；没有clip或改距离/gradient。
- 固定probe samples0/199/399×3、ε=1e−6。point最大误差门1e−7，cover每17索引的诊断FD门1e−5；true smooth/right-left与interval门1e−4原样。不是全部cover分量都FD核验，不能把抽样FD描述成全cover导数证明。
- same query identity只证明roster一致；selected witness/normal变化有独立CSV记录，不能称same nearest feature定理或完整区间支持证书。
- nominal距离可能需要后续QP修复，provider成功仅表示query/选择/梯度诊断成功；row.lower=.005不是所有nominal样本已经安全或controller接受的证明。

## Genuine source20 输入独立只读核验

source20 READY SHA为 `ed369c53267efa139012e5d310a6a8d08db1943bbd46753040da4a0e325bde42`，与输入/程序硬绑定一致。ACTUAL_NOMINAL_Q400_X3.json 为1,581,695 bytes，SHA `e458983841049d2d1cad45373fa4d3743ed9977f644c1cb3576242fcb99d4cff`，3周期各400 samples。

检查extract_genuine_nominal_geometry20.py字段顺序与实际rawForecast writer一致。并使用独立只读binary reader核验三原始original_nominal.bin：每个12,716,651 bytes，SHA与JSON声明匹配；按原字段消费全部value/maps/cycle/cell records到EOF，1200个substep mapped q、genuine value q和JSON round-trip binary64 q逐字相同。原始SHA依次为：

- cycle0 `1b45feecc64093351befdbe318c7268b2c5bc81d1b0b1200893e943bbf41b040`
- cycle1 `bffa5f2f98d1f29e8a2ab72197ff627a8d55aff5fd8e4a9d8a537c9feb3370dd`
- cycle2 `0b0f7d4ef7ce460b8ca8edb1bf1a1c43c8a6292de69dae841c84af6242d411f6`

输入包含原actual initial/history、nominal controls/digest、Model metadata、XML/constants/config/dependency/SDK pins。程序核验joint coordinate names与RobotKinematics一致、raw文件actual SHA、cycle/sample固定时钟和真实成功标志；未生成新future Model状态或伪造mapped q。最终runtime profile仍需明确选择输入原dependencies中的robot/URDF/geometry/assets身份；本轮没有尚未提供的最终profile，故不宣称该profile闭包已审通过。

## 输出 / SDK / 失败

- readPinned通过O_NOFOLLOW、fstat regular/exact bytes、实际打开bytes SHA、EOF后才parse；profile≤2MiB、nominal input≤4MiB。
- Output fresh absolute dir、file O_EXCL/NOFOLLOW/CLOEXEC，统一32MiB写前reserve，四CSV固定名+completion；普通失败保留实际已写prefix，周期性fsync及终止flush。hardkill可能不产生completion或丢失尚未fsync部分，不能从最后prefix推定完整1326范围。
- dependencies启动/正常终止/普通失败cleanup核验；dl_iterate_phdr actual loaded路径须属于profile已pin库，最终实际set等于startup set。它检查实际loader路径与文件身份，不是旧Session的/proc/self/maps inode/device映射证明，也未把SDK名单称完整系统环境。
- 程序实例只有RobotKinematics及Scene（Pinocchio内部Model属于kinematics SDK）；没有Session、augmented ModelF1、MuJoCo或control/physical step实例/调用。宽编译include路径不构成这些API运行。

Parent称24compile-only未运行、25新probe TU编译中；本报告未核验其完成或最终ELF/profile。这是有限recorded-nominal geometry provider诊断，未授权/实现新Model F1、物理步或控制commit，不建立Phase5接受/性能/硬件结论。

Phase5 NOT_ACCEPTED；Phase6 NOT_STARTED。
