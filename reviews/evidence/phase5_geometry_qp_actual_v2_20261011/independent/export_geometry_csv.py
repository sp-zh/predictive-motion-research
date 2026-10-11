"""Export saved actual30 nominal geometry support/minimum fields; no geometry calls."""
from pathlib import Path
import sys,importlib.util,csv
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('own_schema',OUT/'audit_geometry_qp_actual.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
BASE=Path('/private/tmp/phase5_geometry_qp_actual_checkpoint_v1_20261011/actual-dell/session-geometry-qp-three-cycle-v4-20261011-attempt30/run-attempt1/artifacts')
for cycle in range(3):
 p=BASE/f'cycle-{cycle}'/'nominal_geometry_rows.bin';blob=p.read_bytes();g=m.parse_geometry(blob);out=OUT/f'cycle_{cycle}_geometry_minima_supports.csv'
 with out.open('w',newline='') as fd:
  w=csv.writer(fd);w.writerow(['sample','cell','cycle','half','elapsed','min_true_m','min_cover_m','full_query_count']+[f'selected_{i}_{k}' for i in range(4) for k in ['id','distance_m']])
  for sample in g['samples']:w.writerow([sample['sample'],sample['cell'],sample['cycle'],sample['half'],sample['time'],sample['true'],sample['cover'],sample['query_count']]+[v for row in sample['selected'] for v in [row['id'],row['distance']]])
 assert out.stat().st_size<1000000 and p.read_bytes()==blob
