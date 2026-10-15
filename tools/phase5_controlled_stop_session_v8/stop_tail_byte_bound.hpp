#pragma once
#include <cstdint>
namespace phase5_stop_tail_bound_v1 {
// Codec-valid terminal text max1MiB. All earlier successfulC errors empty;
// at mostone failedC (Simulation poisoned, entry exits), one failedhalf.
// Four copies of failedC/half error, two snapshoterrors and three entryerrors.
constexpr std::uint64_t commit_numeric_fixed_and_success_labels=121ULL*5000;
constexpr std::uint64_t stop_records=178ULL*512;
constexpr std::uint64_t snapshots_numeric_fixed=2ULL*73728; // each<=2*4096integration doubles plusallfixedstate/IDs
constexpr std::uint64_t registry=176ULL*256;
constexpr std::uint64_t bootstrap_headers_manifest_receipts=262144;
constexpr std::uint64_t terminal_binary_error_text=9ULL*1048576;
constexpr std::uint64_t yaml_main_error_escape=6ULL*1048576;
constexpr std::uint64_t numerical_working_face_trace=4ULL*1048576; //512 basis/16384 endpoint/1536refinement records, availability and atmostone1MiB failure error
constexpr std::uint64_t maximum_terminal_bytes=commit_numeric_fixed_and_success_labels+stop_records+snapshots_numeric_fixed+registry+bootstrap_headers_manifest_receipts+terminal_binary_error_text+yaml_main_error_escape+numerical_working_face_trace;
constexpr std::uint64_t reserved_terminal_bytes=32ULL*1048576;
static_assert(maximum_terminal_bytes<reserved_terminal_bytes,"bounded actual121 history/178stop points/current/termination/manifest/new4MiB numerical trace fit terminalpool");
}
