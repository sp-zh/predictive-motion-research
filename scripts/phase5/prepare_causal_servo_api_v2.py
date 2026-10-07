#!/usr/bin/env python3
from pathlib import Path
import hashlib,json
p=Path('/home/codextransfer/predictive_motion');old=p/'tools/phase5_causal_servo';new=p/'tools/phase5_causal_servo_v2';new.mkdir(exist_ok=False);freeze=json.loads((p/'results/phase5/development/causal-soft-servo-cpp-v1/frozen.json').read_text())
for name in ['causal_soft_servo.hpp','causal_soft_servo_probe.cpp']:
 source=old/name;assert hashlib.sha256(source.read_bytes()).hexdigest()==freeze['files'][str(source)]
s=(old/'causal_soft_servo.hpp').read_text().replace('void domain(const Vector& z)const {','void domain(const Vector& z)const {\n  validate();')
s=s.replace('model.domain(initial);\n int nx=int(initial.size()),nu=int(control.size());','model.validate();model.domain(initial);\n if(control.size()!=model.n()+1||!control.allFinite())throw std::invalid_argument("control dimension or nonfinite");\n int nx=int(initial.size()),nu=int(control.size());')
(new/'causal_soft_servo.hpp').write_text(s);(new/'causal_soft_servo_probe.cpp').write_text((old/'causal_soft_servo_probe.cpp').read_text())
(new/'CMakeLists.txt').write_text((old/'CMakeLists.txt').read_text()+'''\nadd_executable(causal_soft_servo_api_probe causal_soft_servo_api_probe.cpp)
target_compile_features(causal_soft_servo_api_probe PRIVATE cxx_std_17)
target_compile_options(causal_soft_servo_api_probe PRIVATE -Wall -Wextra -Werror)
target_link_libraries(causal_soft_servo_api_probe PRIVATE Eigen3::Eigen)
''');print('isolated v2 prepared; v1 unchanged')
