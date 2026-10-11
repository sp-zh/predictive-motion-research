# Actual36 receipt-count correction

The correct total is **59 unique lossless manifest receipts: parent8 +3×17**. The prior sealed review's “62” in REVIEW.md and agent messages was a documentation error. Its underlying STAGE1_RESULT.json already records the correct8/17/17/17 counts; the checker did not calculate62.

Each cycle's actual_task_errors.bin is already included in that cycle's17 manifest entries. Three additional reads for task-metric parsing are verification/read occurrences, not new receipts. They must not be added to the unique receipt count.

The original25-payload review READY `0e255995ed9c762085b38fae8cc2e8e6e58c53d45bd7a1fef33ccde07f6e5f4d` and every payload were checked unchanged and are preserved. This supplement supersedes only its receipt count. Algebra, SI/history/B/C/TCP conclusions and limitations remain unchanged. No matrix, native, Model, solver, compiler, FK, Scene or SSH rerun occurred; the human pause remains in force.
