# Ahead5 exception-to-PASS 定向复核

范围仅为 immutable Ahead4→Ahead5 的三个源码文件差异及对应清单身份；未修改项目源码、未编译或执行 native、未跨聊天发送消息。

结论：此前 exception-to-PASS finding 已修复。本次定向复核未发现新的必须修复问题；这不是运行结果或 Phase5 验收。

## 身份

- Ahead5 READY SHA-256：`7495e8ecd0bf8c169eda2eb3bd18471e0bc48c556390bd6ae5eac54a86b9dc97`，26 个列明文件的字节数和 SHA 全部匹配。
- Runtime profile5 READY SHA-256：`33d334ceee86b4a84441c38061564a1261a2e2147c325b7632b5837c43923df7`，9 个列明文件全部匹配。
- 相较 Ahead4，src 目录仅 `candidate_validation.cpp`、`runtime_observer.cpp`、`active_first_cycle.cpp` 改变。运行计划包含这三个当前文件的对应字节数/SHA。

## 修复确认

- `candidate_validation.cpp:27–28`：先完成可能分配内存的成功 stage 赋值，再设置 `passed=true`；标准异常 catch 首先清除 passed。异常诊断自身再次抛出时，成功标志也已清除，异常会向外传播。
- `runtime_observer.cpp:126`：私有 token 创建要求 passed 且 error 为空。
- `runtime_observer.cpp:156–158`：先计算两个 checked next counters 并完成成功 stage 赋值，再发布 accepted history；最后才设置 success。发布段仅包含固定长度 `std::array<double,7>`、标量及双整数 BoundaryId 的复制，不涉及动态分配。两个 catch 均首先清除 success，因此成功 stage 分配/计数检查失败时，accepted history 尚未发布，原 HISTORY_UNPUBLISHED 失败描述与此路径相符。
- `active_first_cycle.cpp:89,100`：组件继续条件与进程返回 0 条件都同时要求 commit success 和内部 error 为空。

差异未更改数学运算、物理两子步、原安全门、原 SI/strict/nativeSOLVED 条件或资源限制。此前 Ahead4 报告所述最佳努力失败证据收集限制仍属原有范围，本次未扩展重审。
