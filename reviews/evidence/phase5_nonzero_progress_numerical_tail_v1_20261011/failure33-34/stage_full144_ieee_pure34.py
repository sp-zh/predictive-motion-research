from pathlib import Path
import json,hashlib,subprocess,shlex
D=Path('/private/tmp/phase5_full144_ieee_pure_active_v1_20261011');remote='/home/codextransfer/predictive_motion/results/phase5/full144-ieee-terminal-pure-v1-20261011-attempt34';files={'src/progress_numeric_forensics.cpp':(D/'progress_numeric_forensics.cpp').read_text(),'src/current_numeric_guess.hpp':Path('/private/tmp/phase5_nonzero_progress_source_review_v1_20261011/src/current_numeric_guess.hpp').read_text()};ids=[{'requested_path':remote+'/'+n,'bytes':len(b.encode()),'sha256':hashlib.sha256(b.encode()).hexdigest()} for n,b in files.items()];argv=[['/usr/bin/x86_64-linux-gnu-g++-13','-I',remote+'/src','-I','/usr/include/eigen3','-std=c++17','-O2','-DNDEBUG','-fno-fast-math','-ffp-contract=off','-Wall','-Wextra','-Wpedantic','-MMD','-MF',remote+'/build-attempt1/unit-1.d','-c',remote+'/src/progress_numeric_forensics.cpp','-o',remote+'/build-attempt1/unit-1.o'],['/usr/bin/x86_64-linux-gnu-g++-13',remote+'/build-attempt1/unit-1.o','-o',remote+'/build-attempt1/progress_numeric_forensics']];plan={'schema':'ACTIVE_SESSION_PILOT_BC_COMPILE_V1','output_directory':remote+'/build-attempt1','env':{'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C','TZ':'UTC'},'input_files':ids,'readonly_directory_rosters':[],'compile_argv':argv};runner=Path('/private/tmp/phase5_task_start_a_active_v1_20261010/dev_compile.py').read_text().replace('ACTIVE_SESSION_A_COMPILE_V1','ACTIVE_SESSION_PILOT_BC_COMPILE_V1');files.update({'dev_compile.py':runner,'dev_compile_plan.json':json.dumps(plan,indent=2)+'\n'});s='''from pathlib import Path
import json,sys
p=Path(%r);p.mkdir(exist_ok=False);(p/'src').mkdir()
for n,b in json.load(sys.stdin).items():
 with (p/n).open('x') as f:f.write(b)
print('Fresh pure Eigen forensics compiler+link staged; no SDK/native control')
'''%remote;x=subprocess.run(['tools/dell-ssh.sh','-T','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','DellTransfer','python3 -I -S -B -c '+shlex.quote(s)],input=json.dumps(files).encode(),capture_output=True,timeout=25);assert x.returncode==0,x.stderr
for n,b in files.items():
 q=D/n;q.parent.mkdir(exist_ok=True);q.write_text(b)
(D/'REMOTE.json').write_text(json.dumps({'remote':remote})+'\n');print(x.stdout.decode())
