# ResourcePlan pricing verification figure

`plot_pricing_bounded85.py` reads the independently accepted runtime review,
actual stdout and the original fixed pricing roster. It partitions all 85
observed groups into 51 accepts and 34 required first-condition refusals:
2 live-quota, 11 output-quota and 21 domain/enum refusals. Refusal groups pass
only when the test checks the expected first `invalid_argument` reason.
Each bar reports passing groups over the frozen group count.

The renderer never invokes the project executable. Use Python 3.12 and
Matplotlib 3.10.3, a fresh output directory and temporary writable font/cache
paths. From the repository root:

```sh
python tools/phase5_foundation_verification_visuals/plot_pricing_bounded85.py \
  --review reviews/evidence/public_live_affine_v2_resource_pricing_bounded85_runtime_once_v1_20261009/ROOT_PRICING_RUNTIME85_REVIEW.json \
  --stdout reviews/evidence/public_live_affine_v2_resource_pricing_bounded85_runtime_once_v1_20261009/PRICING_BOUNDED85_STDOUT.txt \
  --roster reviews/evidence/public_live_affine_v2_foundation_resource_pricing_source_protocol_v1_20261009/FIXED_PRICING_CASES_AND_DIMENSIONAL_LEDGER_V1.json \
  --output-dir /tmp/resource-pricing-bounded85-figure-reproduction
```

The PNG is 2340 × 1260; the SVG retains editable text. Provenance records exact
source and output hashes, font, dimensions, color and renderer version. Direct
labels preserve meaning in grayscale. No timing, memory or motion data is
plotted. These are finite public getter/refusal checks; private banks,
independent matrix/cumulative-cap refusals and exact writer bytes retain their
recorded limitations. Phase5 remains NOT_ACCEPTED and Phase6 NOT_STARTED.
