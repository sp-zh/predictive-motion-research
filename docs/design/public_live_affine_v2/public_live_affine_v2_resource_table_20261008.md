# Prospective integer shape accounting (not runtime evidence)

All numeric slots are conservatively priced as 8 bytes, including integers. Raw Map includes its three topology integers (2441 slots). Normalized wholecell/prefix blocks include three/five index slots. Actual encoded metadata, descriptors and strings are independently bounded to 8 MiB.

`SDKplanning_allowance_only = 3*raw + 1,000,000` is a logical admission allowance. It is not a proven SDK allocation or process RSS bound. Tracked numeric slots exclude STL capacity overhead, strings and opaque SDK/process allocations; metadata has its own actual byte guard.

Maximum factor envelope: K=32 terms, R=8192 total rows, each term at most 256 rows, 4,000,000 sample-addition coefficient slots, 8192 addition records.

Owned buffers / planning allowances

| Buffer (numeric slots unless bytes specified) | N20/T200 | N20/T375 | N32/T375 |
|---|---:|---:|---:|
| model_result_base | 1541030 | 2846005 | 2875765 |
| SDKplanning_allowance_only | 5623090 | 9538015 | 9627295 |
| normalized_native_blocks | 522020 | 957070 | 971962 |
| boundary_o_M_P | 120330 | 120330 | 284130 |
| T_and_t | 127190 | 127190 | 320222 |
| full_factor_and_addition_input | 10671286 | 10671286 | 14421430 |
| term_sum_and_direct_evaluation_work | 1328000 | 1328000 | 2438144 |
| prefix_stream_work | 22860 | 22860 | 34380 |
| term_and_sum_condensed_capture | 2169815 | 2169815 | 4277759 |

Raw model base is included in SDK planning allowance and is not summed twice. The reusable term/sum/direct-evaluation workspace covers streamed canonical sums, both direct/condensed gradients and Hessians, matrix products and finite guards. Sum factor rows stream within per-term row work; no R-row scratch is assumed.

Complete plans

| Buffer (numeric slots unless bytes specified) | N20/T200 | N20/T375 | N32/T375 |
|---|---:|---:|---:|
| compact_reserved_numeric_slots | 20584591 | 24934566 | 32375322 |
| compact_reserved_bytes | 164676728 | 199476528 | 259002576 |
| dense_audit_reserved_numeric_slots | 39183331 | 55839306 | 84419262 |
| complete_compact_output_numeric_slots | 23350287 | 25090312 | 37712908 |
| complete_compact_binary_byte_bound | 195190904 | 209111104 | 310091872 |
| complete_compact_json_byte_bound | 802298366 | 861459216 | 1290627480 |

DenseAudit additional buffers

| Buffer (numeric slots unless bytes specified) | N20/T200 | N20/T375 | N32/T375 |
|---|---:|---:|---:|
| L_E_f_initial_selector | 517230 | 517230 | 1264230 |
| elimination_workspace | 3897180 | 3897180 | 9545580 |
| X_control_offset_initial | 120330 | 120330 | 284130 |
| sample_dense_selectors | 9480000 | 17775000 | 28035000 |
| sample_explicit_recursive_and_eliminated_views | 4584000 | 8595000 | 12915000 |

The proposed 64,000,000 live numeric-slot cap admits these compact planning reservations. N32 DenseAudit exceeds it and must refuse. N32 full-factor binary capture also exceeds 256 MiB and must refuse. N20 full-factor binary capture fits the prospective byte plan; full numeric JSON exceeds 256 MiB and must refuse. Actual metadata/byte guards still apply. No field omission or automatic quota increase is allowed.

Smaller cost shapes illustrate conditional admission only: K=8, R=1024, C=200000, 1000 records. They are not task weights or research results.
N20/T200: compact bytes 73343776, binary output bound 48454368, JSON bound 178668088.
N20/T375: compact bytes 108143576, binary output bound 62374568, JSON bound 237828938.

Tracked cumulative copy/scratch-use planning charge

| Buffer (numeric slots unless bytes specified) | N20/T200 | N20/T375 | N32/T375 |
|---|---:|---:|---:|
| cumulative_wrapper_charge_upper | 124721871 | 137072846 | 189788354 |
| dense_cumulative_wrapper_charge_upper | 143320611 | 167977586 | 241832294 |

Formula: compact reservation + S*prefix work + (K+1)*term/sum/direct-evaluation work + 8*C + 2*records*(900+240+30). DenseAudit adds its extra buffers. The K+1 output evaluation blocks include the canonical sum and may not alias term evaluations with different floating point accumulation paths. Every actual tracked charge must remain within its planned ceiling and hard cap; implementation must refuse unplanned scratch. This integer arithmetic is not Model execution or a measurement of SDK heap/RSS.
