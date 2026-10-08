# Prospective integer shape accounting (not runtime evidence)

All numeric slots are conservatively priced as8 bytes, including integers.
Model scratch/growth reservation is a planning allowance; it is NOT an instrumented SDK allocator bound.
Maximum factor envelope uses K32 terms/R8192 total rows/perterm r<=256,
4m sample-addition coefficient slots and8192 addition records.

| Buffer (numeric slots) | N20/T200 | N20/T375 | N32/T375 |
|---|---:|---:|---:|
| model_result_base | 1539170 | 2842570 | 2872294 |
| model_growth_and_sdk_reservation | 5617510 | 9527710 | 9616882 |
| normalized_native_blocks | 519960 | 953260 | 968116 |
| boundary_o_M_P | 120330 | 120330 | 284130 |
| T_and_t | 127190 | 127190 | 320222 |
| full_factor_and_addition_input | 10671286 | 10671286 | 14421430 |
| term_transform_product_work | 1328000 | 1328000 | 2438144 |
| prefix_stream_work | 22860 | 22860 | 34380 |
| term_and_sum_condensed_capture | 2169815 | 2169815 | 4277759 |

Raw model base is included in the3*raw+1m reservation, not summed twice.

| Plan | N20/T200 | N20/T375 | N32/T375 |
|---|---:|---:|---:|
| compact_reserved_numeric_slots | 20576951 | 24920451 | 32361063 |
| compact_reserved_bytes | 164615608 | 199363608 | 258888504 |
| dense_audit_reserved_numeric_slots | 39175691 | 55825191 | 84405003 |
| complete_compact_output_numeric_slots | 23294843 | 25031543 | 37574003 |
| complete_compact_binary_byte_bound | 194747352 | 208640952 | 308980632 |
| complete_compact_json_byte_bound | 800413270 | 859461070 | 1285904710 |

| DenseAudit extra buffer | N20/T200 | N20/T375 | N32/T375 |
|---|---:|---:|---:|
| L_E_f_initial_selector | 517230 | 517230 | 1264230 |
| elimination_workspace | 3897180 | 3897180 | 9545580 |
| X_control_offset_initial | 120330 | 120330 | 284130 |
| sample_dense_selectors | 9480000 | 17775000 | 28035000 |
| sample_explicit_recursive_and_eliminated_views | 4584000 | 8595000 | 12915000 |

Proposed64m live-slot limit admits these compact retention plans. DenseAudit N32
exceeds it and MUST refuse; full-cost N32 binary complete-output also exceeds
256MiB and MUST refuse. N20 max-factor cases fit binary complete-output; JSON
all-number expansion exceeds256MiB and MUST refuse. No dropping fields or auto
raising quota is allowed.

Illustrative smaller-cost admission shapes only: K8/R1024/C200k/1000 addition
records. They are not selected task weights or research outcomes.
N20/T200: compact bytes73282656, complete binary output bound48010816, JSON bound176782992.
N20/T375: compact bytes108030656, complete binary output bound61904416, JSON bound235830792.

Tracked cumulative copy/scratch-use upper planning charge (not all SDK allocator activity):

| Plan | N20/T200 | N20/T375 | N32/T375 |
|---|---:|---:|---:|
| cumulative_wrapper_charge_upper | 123386231 | 135730731 | 187335951 |
| dense_cumulative_wrapper_charge_upper | 141984971 | 166635471 | 239379891 |

Formula: compact reservation + S*prefix_stream_work + K*term_transform_work + 8*C_addition + 2*addition_records*(900+240+30); DenseAudit adds its declared extra buffers. Every actual tracked charge is bounded by this precomputed planned ceiling and hard cap; source implementation must validate this schedule and reject unplanned scratch, not assume empirical success.
