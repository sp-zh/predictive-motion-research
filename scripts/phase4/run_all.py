"""Run development then untouched evaluation on one immutable protocol/source snapshot."""
from pathlib import Path
import json,hashlib,subprocess,time,sys,os
import yaml
root=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[2]
config=yaml.safe_load((root/'config/phase4.yaml').read_text())
epoch=sys.argv[3] if len(sys.argv)>3 else 'frozen-v3'
raw_root=Path(sys.argv[2]) if len(sys.argv)>2 else Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase4/raw')/epoch
results=root/'results/phase4'/epoch;results.mkdir(parents=True,exist_ok=True)
files=[root/'config/phase4.yaml',root/'experiments/generated/phase4/geometry.json',
       root/'benchmarks/reference/inspection_curve.json',root/'experiments/generated/inspection/scene.xml',
       root/'experiments/generated/inspection/inspection_fr3.xml']
files+=list((root/'tools/phase4_adapters').glob('*.cpp'))+list((root/'tools/phase4_adapters').glob('*.hpp'))
files+=list((root/'tools/phase4_servo').glob('*'))
files+=[root/'tools/phase4_adapters/CMakeLists.txt',root/'build-phase4-adapters/phase4_benchmark',root/'build-phase4-servo/servo_sidecar']
files+=list((root/'src/predictive_motion_control/src').glob('*.cpp'))
files+=list((root/'src/predictive_motion_control/include/predictive_motion_control').glob('*.hpp'))
frozen={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
manifest={'files':frozen,'config':config,'raw_root':str(raw_root),'code_epoch':epoch,
          'prior_development':'development and frozen-v2: prior traces preserved; v3 repairs unsigned initialization sequence, no parameter tuning; evaluation previously untouched',
          'start_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
freeze=results/'frozen.json'
if freeze.exists():raise SystemExit('Refuse freeze overwrite')
freeze.write_text(json.dumps(manifest,indent=2)+'\n')
progress=[]
for split,seeds in [('development',config['development_seeds']),('evaluation',config['evaluation_seeds'])]:
    for seed in seeds:
        for method in config['methods']:
            for name,digest in frozen.items():
                if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:raise RuntimeError('Source/config changed after freeze: '+name)
            output=raw_root/split/f'{method}_{seed}.csv'
            report=results/split/f'{method}_{seed}.yaml'
            output.parent.mkdir(parents=True,exist_ok=True);report.parent.mkdir(parents=True,exist_ok=True)
            begin=time.monotonic()
            cmd=[str(root/'build-phase4-adapters/phase4_benchmark'),str(root),str(root/'config/phase4.yaml'),method,str(seed),split,str(output),str(report)]
            completed=subprocess.run(cmd,text=True,capture_output=True,timeout=600)
            stem=results/split/f'{method}_{seed}'
            stem.with_suffix('.stdout').write_text(completed.stdout);stem.with_suffix('.stderr').write_text(completed.stderr)
            entry={'method':method,'seed':seed,'split':split,'exit_code':completed.returncode,'wall_seconds':time.monotonic()-begin,'raw_file':str(output),'report':str(report)}
            if report.exists():entry.update(yaml.safe_load(report.read_text()))
            progress.append(entry);(results/'progress.json').write_text(json.dumps(progress,indent=2)+'\n')
            print(json.dumps(entry),flush=True)
            if completed.returncode:raise SystemExit('Runner execution error; preserve all evidence before repair')
