# File identity and static range verification figure

This figure uses all 24 original groups from the single reviewed test, with exact 714-byte stdout. Its left panel counts groups (9 identity, 15 ranges); its right panel counts controlled wrapper entries (14 identity, 15 ranges), partitioned into four accepted inputs and 25 required refusals. Refusals are successful contract checks. Entry counts do not measure IO, getter, native calls or independent experiments.

The renderer validates the independent review decision, output identity, original roster and observed group records before plotting. PNG/SVG and provenance use Matplotlib 3.10.3, DejaVu Sans, 13×7 inches and 180 DPI. Both color and grayscale exports require visual inspection. SVG text remains editable; its provenance records complete input/output hashes and selection.

Run `plot_identity_static_ranges_bounded24.py` with `--review`, `--stdout`, `--roster`, `--results` and a fresh `--output-dir`. Use the corresponding public runtime evidence directory for the review/stdout/results and the preserved source protocol v3 directory for `FIXED_IDENTITY_RANGE_ROSTER_AND_ORACLE_V1.json`.

The fixtures are synthetic. Exact source checks corroborate expected exception categories, but reasons are not separately printed exception telemetry. These results establish neither robot physical admission nor controller performance, RSS, full native ABI/readset, or phase acceptance. Phase5 remains NOT_ACCEPTED; Phase6 is NOT_STARTED.
