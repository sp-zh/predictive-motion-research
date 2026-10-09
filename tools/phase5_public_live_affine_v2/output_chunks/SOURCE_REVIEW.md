# Source3C2A self review — pending independent static review

Only bounded typed numeric provisional writer and independent readback source
are implemented. Foundation-only static target, no executable or inventory driver.
Binary f64le/u64le/i64le and strict numeric JSON/full failure IEEE bit strings are
explicit; frozen encoding/no fallback, full count/byte/type/SHA/path/EOF/file and
directory identity enforced. No root CAPTURE_READY or mathematical acceptance.

SharedCaseBudget shares original CaseState/BatchState/caps/encoding and survives
wrapper lifetime; Writer24/reader28-slot tickets precede cache/shape allocations and release
after buffers/specs. Writer/readback have separate formatter/parser; hash/path
primitives are shared. Scoped per-case IO reentry latches first failure and prevents
outer closure after swallowed recursion. File creation is first O_EXCL provisional;
all failures remain, no unlink/rename/retry. Actual successful write-stream bytes
and SHA differ deliberately from independently read actual FD SHA; closed_fsynced
is not final content attestation under mutation. Future immutable full closure is
still required.

Concrete draft findings fixed with before-source history: validate all caller
bounds/types/shape/name/SHA/root/caps before owned copy; safe immutable root/shape
snapshot; actual short-write pending frontier advances before possible hash error;
writer scratch charges BEFORE every first byte of cache generation (no flush
recharge), reader before fill. No unbudgeted full numeric cache/DOM is created;
stdfunction arbitrary allocation/copy side effects remain a restricted contract,
not a claim of all-process instrumentation. Case/batch/output/metadata ceilings
are unchanged. Full live/cumulative capture admission has not been proved;3C2B
must redeploy IO from truly unused upstream workspace or refuse.

All configure/compiler/empty/parser/fixture/numeric/matrix/Model/query/rollout/
plant/solver/main/scorer counts0. Static source and SHA review only. Original
Model/checker/freeze/Dell metadata untouched; foundation shared-budget extension
and mandatory compiled-source closure additions preserve accepted before versions.
Phase5 NOT_ACCEPTED; Phase6 NOT_STARTED. No new trajectory/video/performance
result can arise from this source checkpoint. See FORMAT_AND_SCOPE and
INTEGRATION_CONTRACT for exact low-level limits and future full evidence work.

Final fixed-scratch accounting: writer decimal/f64 token32 bytes is charged4
slots BEFORE each token materialization. Reader headerString<=64 and numberToken
<=32 charge8 BEFORE each bounded token materialization (conservative, no full
numeric arrays). Writer IO20 covers cache16+token4; returned move-only record
holds separate4-axis ticket until its spec arrays die, including after writer
return. Custom record move assignment preserves old axes until their ticket dies.
Reader IO28 covers cache16+private axes4+token8; all its arrays die before ticket.
Caller must treat returned receipts immutable and may not reallocate/clone axes
outside its own accounted source metadata; arbitrary STL capacity and callback
capture allocations remain outside the logical payload instrumentation.
Future3C2B must count every token/string/header/read/write generation and persistent
4-slot receipt as well as copied manifest descriptors; no cap grows.
