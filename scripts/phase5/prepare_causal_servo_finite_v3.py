#!/usr/bin/env python3
from pathlib import Path
import hashlib,json
p=Path('/home/codextransfer/predictive_motion');old=p/'tools/phase5_causal_servo_v2';new=p/'tools/phase5_causal_servo_v3';new.mkdir(exist_ok=False);freeze=json.loads((p/'results/phase5/development/causal-soft-servo-cpp-v2/frozen.json').read_text())
for f in old.iterdir():
 assert hashlib.sha256(f.read_bytes()).hexdigest()==freeze['files'][str(f)]
 (new/f.name).write_bytes(f.read_bytes())
s=(new/'causal_soft_servo.hpp').read_text().replace('#include <vector>','#include <vector>\n#include <initializer_list>')
s=s.replace('struct Model {','''template<class Derived>
inline void requireFinite(const Eigen::MatrixBase<Derived>& value,const char* stage) {
 if(!value.allFinite())throw std::overflow_error(stage);
}
inline void requireFinite(std::initializer_list<double> values,const char* stage) {
 for(double value:values)if(!std::isfinite(value))throw std::overflow_error(stage);
}
struct Model {''')
s=s.replace('Vector q=z.head(count),v=z.segment(count,count),e=z.segment(2*count,count)-q;','Vector q=z.head(count),v=z.segment(count,count),e=z.segment(2*count,count)-q;\n  requireFinite(e,"nonfinite derived target error");')
s=s.replace('// All inputs causal:', '''inline void validateTransition(const Transition& t) {
 requireFinite(t.state,"nonfinite returned state");requireFinite(t.A,"nonfinite returned A");
 requireFinite(t.B,"nonfinite returned B");requireFinite(t.defect,"nonfinite returned defect");
}
// All inputs causal:''')
s=s.replace('current(nx-1)+=command_dt*control(n);','current(nx-1)+=command_dt*control(n);\n requireFinite(current,"nonfinite command/progress propagation");')
s=s.replace('int branch=0;if(drive>=eta)', 'requireFinite({smooth,drive},"nonfinite force drive");\n   int branch=0;if(drive>=eta)')
s=s.replace('double gain=physical_dt/(m+physical_dt*D),inside=branch==0?1.:0.;', '''double denominator=m+physical_dt*D;
   requireFinite({denominator},"nonfinite implicit denominator");
   double gain=physical_dt/denominator,inside=branch==0?1.:0.;
   requireFinite({gain,force},"nonfinite physical gain/force");''')
s=s.replace('next(n+j)=v+gain*(smooth+force);next(j)=q+physical_dt*next(n+j);','requireFinite({dvq,dvv},"nonfinite physical derivative");\n   next(n+j)=v+gain*(smooth+force);next(j)=q+physical_dt*next(n+j);\n   requireFinite({next(n+j),next(j)},"nonfinite physical state propagation");')
s=s.replace('Vector f=next-P*current;out.A=(P*out.A).eval();out.B=(P*out.B).eval();out.defect=(P*out.defect+f).eval();', '''requireFinite(P,"nonfinite physical Jacobian");
  Vector f=next-P*current;requireFinite(f,"nonfinite physical affine defect");
  out.A=(P*out.A).eval();requireFinite(out.A,"nonfinite cycle A propagation");
  out.B=(P*out.B).eval();requireFinite(out.B,"nonfinite cycle B propagation");
  out.defect=(P*out.defect+f).eval();requireFinite(out.defect,"nonfinite cycle defect propagation");''')
s=s.replace('out.state=current;return out;','out.state=current;validateTransition(out);return out;')
s=s.replace('out.A=(t.A*out.A).eval();out.B=(t.A*out.B+t.B).eval();out.defect=(t.A*out.defect+t.defect).eval();out.state=t.state;', 'out.A=(t.A*out.A).eval();requireFinite(out.A,"nonfinite cell A propagation");out.B=(t.A*out.B+t.B).eval();requireFinite(out.B,"nonfinite cell B propagation");out.defect=(t.A*out.defect+t.defect).eval();requireFinite(out.defect,"nonfinite cell defect propagation");out.state=t.state;')
s=s.replace(' return out;\n}', ' validateTransition(out);return out;\n}')
(new/'causal_soft_servo.hpp').write_text(s)
cli=new/'causal_soft_servo_probe.cpp';s=cli.read_text().replace('const Matrix& a){out', 'const Matrix& a){requireFinite(a,"nonfinite matrix serialization");out').replace('const Vector& v){out','const Vector& v){requireFinite(v,"nonfinite vector serialization");out')
s=s.replace('offsets.push_back(t.A*offsets.back()+t.defect);Matrix nextmap=t.A*maps.back();nextmap.block(0,k*nu,nx,nu)+=t.B;maps.push_back(nextmap);initial_maps.push_back(t.A*initial_maps.back());', '''Vector nextoffset=t.A*offsets.back()+t.defect;requireFinite(nextoffset,"nonfinite horizon offset");offsets.push_back(nextoffset);
    Matrix nextmap=t.A*maps.back();requireFinite(nextmap,"nonfinite horizon control sensitivity product");nextmap.block(0,k*nu,nx,nu)+=t.B;requireFinite(nextmap,"nonfinite horizon control sensitivity");maps.push_back(nextmap);
    Matrix nextinitial=t.A*initial_maps.back();requireFinite(nextinitial,"nonfinite horizon initial sensitivity");initial_maps.push_back(nextinitial);''')
cli.write_text(s)
with (new/'CMakeLists.txt').open('a') as f:f.write('''
add_executable(causal_soft_servo_overflow_probe causal_soft_servo_overflow_probe.cpp)
target_compile_features(causal_soft_servo_overflow_probe PRIVATE cxx_std_17)
target_compile_options(causal_soft_servo_overflow_probe PRIVATE -Wall -Wextra -Werror)
target_link_libraries(causal_soft_servo_overflow_probe PRIVATE Eigen3::Eigen)
add_executable(root_edge_probe root_edge_probe.cpp)
target_compile_features(root_edge_probe PRIVATE cxx_std_17)
target_compile_options(root_edge_probe PRIVATE -Wall -Wextra -Werror)
target_link_libraries(root_edge_probe PRIVATE Eigen3::Eigen)
''')
print('v3 prepared; all v2 source hashes remain unchanged')
