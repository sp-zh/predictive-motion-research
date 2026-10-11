Source42 v2 narrow confirmation

The production success latch now appears immediately after commit return, before receipt/write/observe/timing. Standard downstream failures retain physical_commit_completed and completedCommit; the final entry exit condition begins with error.empty(), so they cannot become PASS. The whole summary now calls4ms a diagnostic deadline threshold.

An independent pure regression TU was prepared with verbatim actual Envelope/Ledger, checkedAdd, and production latch. It injects four downstream standard failures and checks actual counters and final failure, plus partial-C no-success. It is not a complete entry/runtime regression. Source and prepared artifact hashes are in RESULT.json.

NOT RUN: required AS1GiB could not be installed on Mac via resource.setrlimit(RLIMIT_AS); both hard+soft and soft-only attempts raised ValueError. The subprocess failed in preexec before executing clang. CPU10s/AS1GiB/overall15s were not relaxed. No compilation, test, Model, OSQP, or physical execution occurred. Prepared regression.cpp can be dispatched under the specified limits on Linux.
