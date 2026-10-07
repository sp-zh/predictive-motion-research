#!/usr/bin/env python3
"""Create versioned metadata; collector-consumed values remain unchanged."""
from pathlib import Path
import yaml
p=Path('/home/codextransfer/predictive_motion')
cfg=yaml.safe_load((p/'config/phase5_development/public_coupled_validation_91013.yaml').read_text())
cfg.update(scope='Replacement schema2 prospective seed91013 known-input development protocol; original consumed collector inputs unchanged',scorer_source=str(p/'scripts/phase5/score_public_coupled_validation_91013_v2.py'),new_shared_stop_cycle_range=[1,1250],criterion='Strict complete capture/all-attempt integrity and warmup/window/regime failure rejection, active original short/long limits; no Phase5 acceptance')
dest=p/'config/phase5_development/public_coupled_validation_91013_v2.yaml'
with dest.open('x') as f:yaml.safe_dump(cfg,f,sort_keys=False)
print(dest)
