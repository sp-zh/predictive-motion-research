# Frozen cold-storage verifier sources

These are the exact small verification sources used for the authorized52/53
shipping-archive moves. They run only with their fixed sidecars in the cold
directory. `strict_codec_reader.py` is data-only; no model or experiment runs.

`validate_cold52_v1.py` is retained as a failed verifier: its53-style same-name
assumption does not apply to52. The separate v2 binds Root's explicit2148-member
mapping and preserves the original failure. Neither source changes historical
READY files or archive bytes. See the [verified storage checkpoint](../../reviews/evidence/phase5_cold_storage_and_bounded_Mac_v1_20261015/README.md).
