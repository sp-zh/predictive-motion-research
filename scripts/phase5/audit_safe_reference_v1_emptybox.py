#!/usr/bin/env python3
"""Read-only captured safe-reference v1 empty-box diagnostic; no plant, fit or guard change."""
import argparse,csv,hashlib,json,math
from fractions import Fraction
from pathlib import Path
SOURCE_SHA=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
import numpy as np
import yaml

RAW_SHA='561d63684b3acc591acf2f287e6f7f264a340207cebe8767887b5107dadc661c'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def continuation(w,a,cap,jerk,dt,side):
    # Necessary speed-only signed cone. No position/geometry/physical stopping certificate.
    r=cap+side*w;acc=side*a;decrease=0.;steps=[];j=1
    while acc+j*jerk*dt<0:
        future=acc+j*jerk*dt;steps.append(future);decrease-=dt*future;j+=1
        assert j<1000
    return {'side':'lower' if side==1 else 'upper','shifted_speed_rad_s':r,
            'fastest_recovery_future_acceleration_rad_s2':steps,
            'required_speed_reserve_rad_s':decrease,'necessary_continuation_margin_rad_s':r-decrease}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--project',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();root=args.project
    case=root/'results/phase5/development/servo-safe-reference-v1-validation';freeze=json.loads((case/'frozen.json').read_text());exe=json.loads((case/'execution.json').read_text());material=json.loads((case/'materialized-identity.json').read_text());store=Path(material['content_store']);rawdir=Path(exe['argv'][-1])
    assert sha(rawdir/'raw.csv')==RAW_SHA and exe['return_code']==3
    inputs=[case/name for name in ['frozen.json','execution.json','materialized-identity.json']]
    for name,h in exe['raw_files'].items():assert sha(rawdir/name)==h;inputs.append(rawdir/name)
    def blob(suffix):
        entries=[(path,h) for path,h in freeze['files'].items() if path.endswith(suffix)];assert len(entries)==1
        path,h=entries[0];p=store/h;assert sha(p)==h;inputs.append(p);return p,path
    source,source_path=blob('/tools/phase5_servo_reference/servo_safe_reference_fixture.cpp')
    proto,proto_path=blob('/config/phase5_development/servo_validation_safe_reference_v1.yaml')
    reference,reference_path=blob('/results/phase5/development/servo-safe-reference-v1/accepted_target_increments.csv')
    identity,identity_path=blob('/results/phase5/development/servo-safe-reference-v1/reference_identity.json')
    cache,cache_path=blob('/build-servo-safe-reference-v1/CMakeCache.txt')
    cfg=yaml.safe_load(proto.read_text());dt=cfg['control_dt_s'];cap=cfg['command_velocity_rad_s'];amax=cfg['command_acceleration_rad_s2'];jerk=cfg['command_jerk_rad_s3'];assert dt==.004 and cap==.0625 and amax==1 and jerk==20
    text=source.read_text();assert 'request=(desired-history.accepted_position)/dt;' in text and 'initial+offsets.at(std::min(tick,int(offsets.size()-1)))' in text
    rows=list(csv.DictReader((rawdir/'raw.csv').open()));cycles=list(csv.DictReader((rawdir/'cycles.csv').open()));refs=list(csv.DictReader(reference.open()));assert len(refs)==928 and len(rows)==1586 and int(rows[-1]['tick'])==792
    vec=lambda r,p:np.array([float(r[p+str(j)]) for j in range(7)])
    final=rows[-1];w,a,c=vec(final,'command_velocity_'),vec(final,'command_acceleration_'),vec(final,'target_');initial=vec(rows[0],'target_');tick=int(final['tick'])+1
    desired=initial+vec(refs[tick],'c_delta_');request=(desired-c)/dt
    arrays=lambda prefix:{key:np.loadtxt(rawdir/(prefix+key+'.csv'),delimiter=',',ndmin=2) for key in ['H','g','A','lower','upper']}
    primary,stop=arrays('first_rejected_'),arrays('stop_')
    assert np.array_equal(primary['A'][:21],stop['A'][:21]) and np.array_equal(primary['lower'][:21],stop['lower'][:21]) and np.array_equal(primary['upper'][:21],stop['upper'][:21])
    assert np.array_equal(primary['H'],np.eye(7)) and np.array_equal(stop['H'],np.eye(7)) and np.max(abs(stop['g']))==0
    assert np.max(abs(primary['g'].ravel()+request))<1e-12
    lo=primary['lower'].ravel();hi=primary['upper'].ravel();empty=np.flatnonzero(lo>hi);assert empty.tolist()==[3]
    lower_text=(rawdir/'first_rejected_lower.csv').read_text().splitlines()[3];upper_text=(rawdir/'first_rejected_upper.csv').read_text().splitlines()[3]
    exact_gap=Fraction(lower_text)-Fraction(upper_text)
    nexta=(a[3]-jerk*dt,a[3]+jerk*dt);nextw=(w[3]+dt*nexta[0],w[3]+dt*nexta[1])
    assert lo[3]==-cap and abs(hi[3]-nextw[1])<1e-15 and exact_gap>Fraction('1e-7')*2
    history=[];maxprojection=0.;first_cone=None
    for t in range(500,793):
        previous=rows[2*t-1];current=rows[2*t+1]
        pc,pw,pa=vec(previous,'target_'),vec(previous,'command_velocity_'),vec(previous,'command_acceleration_');noww=vec(current,'command_velocity_');nowa=vec(current,'command_acceleration_')
        target=initial+vec(refs[t],'c_delta_');asked=(target-pc)/dt
        low=np.maximum.reduce([-np.ones(7)*cap,pw-amax*dt,pw+dt*pa-jerk*dt*dt]);high=np.minimum.reduce([np.ones(7)*cap,pw+amax*dt,pw+dt*pa+jerk*dt*dt]);assert np.all(low<=high)
        maxprojection=max(maxprojection,float(np.max(abs(noww-np.clip(asked,low,high)))))
        for j in range(7):
            for side in [1,-1]:
                cone=continuation(noww[j],nowa[j],cap,jerk,dt,side)
                if cone['necessary_continuation_margin_rad_s']<-1e-10 and first_cone is None:first_cone={'tick':t,'joint':j,'accepted_w_rad_s':float(noww[j]),'accepted_alpha_rad_s2':float(nowa[j]),**cone}
        if t in [695,725,750,775,780,785,790,792]:
            history.append({'tick':t,'axis3_reference_delta_rad':float(refs[t]['c_delta_3']),'axis3_accepted_delta_rad':float(vec(current,'target_')[3]-initial[3]),'axis3_reference_position_debt_rad':float(target[3]-vec(current,'target_')[3]),'axis3_reference_velocity_rad_s':float(refs[t]['w_reference_3']),'axis3_accepted_velocity_rad_s':float(noww[3]),'axis3_accepted_acceleration_rad_s2':float(nowa[3])})
    assert first_cone['tick']==785 and first_cone['joint']==3 and maxprojection<1e-7
    summary=yaml.safe_load((rawdir/'summary.yaml').read_text());assert not summary['completed_stop'] and 'NO_FEASIBLE_STOP' in summary['stop_failure']
    assert all(r['phase'] in ['warmup','excitation'] for r in rows) and cycles[-1]['status']==summary['stop_failure']
    result={'scope':__doc__,'verdict':'VERIFIED_CAPTURED_EMPTY_COMMAND_BOX_NOT_STOPPING_PASS','source_sha256':SOURCE_SHA,'original_raw_sha256':RAW_SHA,'rows':len(rows),'last_accepted_tick':792,'rejected_tick':793,'final_time_s':float(final['time_s']),'empty_captured_rows':empty.tolist(),'axis3':{'last_accepted_w_rad_s':float(w[3]),'last_accepted_alpha_rad_s2':float(a[3]),'permitted_next_alpha_rad_s2':list(nexta),'permitted_next_w_from_acceleration_jerk_rad_s':list(nextw),'speed_cap_rad_s':cap,'captured_lower_rad_s':float(lo[3]),'captured_upper_rad_s':float(hi[3]),'exact_decimal_gap_rad_s':float(exact_gap),'exact_gap_positive':True,'gap_after_both_row_1e7_allowances_rad_s':float(exact_gap-Fraction('2e-7')),'reference_w_at_reject_rad_s':float(refs[tick]['w_reference_3']),'deadbeat_position_request_at_reject_rad_s':float(request[3]),'reference_position_debt_before_reject_rad':float(desired[3]-c[3]),'signed_lower_cone':continuation(w[3],a[3],cap,jerk,dt,1)},'first_accepted_state_outside_necessary_signed_speed_cone':first_cone,'recorded_reference_catchup_samples':history,'max_recorded_velocity_difference_from_command_only_clamped_request_rad_s':maxprojection,'primary_stop_first21rows_identical':True,'primary_stop_shapes':[list(primary['A'].shape),list(stop['A'].shape)],'stop_objective_zero_gradient':True,'no_post_rejection_physical_substeps_or_accepted_stop_commands':True,'final_recorded_physical_speed_rad_s':float(max(abs(vec(final,'v_post_')))),'final_cycle':cycles[-1],'producer_summary':summary,'frozen_actor_source':{'original_path':source_path,'sha256':sha(source),'cache_original_path':cache_path,'cache_sha256':sha(cache),'identity_basis':'Read immutable frozen blobs, not currently edited developer files/CMake'},'reference_identity':json.loads(identity.read_text()),'effective_inputs':{str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in inputs}}
    assert sha(Path(__file__))==SOURCE_SHA
    args.output.mkdir(parents=True,exist_ok=False);(args.output/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
    note=f'''# Safe-reference v1 empty command box

Verdict: VERIFIED_CAPTURED_EMPTY_COMMAND_BOX_NOT_STOPPING_PASS. No plant/fitting/guard change or current developer source/CMake was used. Raw SHA{RAW_SHA}; actor source frozen blob SHA{sha(source)}. Original output and capture are retained; this is not a general stopping guarantee or a reversal of progress RET002.

There are1586 physical records through accepted tick792/time{float(final['time_s']):.3f}s. Both actual primary and stop QPs at tick793 have the same21 command rows; row3 (joint4, zero-based axis3) is empty. Its lower is speed cap -{cap}, while upper is {hi[3]:.17g}. Exact stored-decimal contradiction is {float(exact_gap):.14g}rad/s and remains positive after1e-7 allowances on both rows. Geometry cannot repair an already empty command interval, and changing the stop objective cannot repair it.

Last accepted w={w[3]:.17g}rad/s and alpha={a[3]:.17g}rad/s². With dt=.004 and jerk20, nextalpha lies[{nexta[0]:.14g},{nexta[1]:.14g}], hence nextw lies[{nextw[0]:.14g},{nextw[1]:.14g}], wholly below -.0625. The tight lower is the speed cap and upper is the jerk-history bound; position caps/geometry are not needed for this contradiction. The previous accepted command respected instantaneous speed but had no speed-only continuation.

For the lower signed speed limit define r=w+V in[0,2V], retaining the same acceleration and jerk. The fastest future recovery of negative acceleration is alpha_j=min(0,alpha+j*J*dt). A necessary continuation condition is r>=-dt*sum(alpha_j). It is not sufficient for position/geometry/physical-servo safety. The first already accepted speed-only-unviable record is tick{first_cone['tick']}, axis{first_cone['joint']}: w={first_cone['accepted_w_rad_s']:.14g}, alpha≈-1, reserve{first_cone['shifted_speed_rad_s']:.14g}, required reserve{first_cone['required_speed_reserve_rad_s']:.14g}. Upper-limit continuation uses r=V-w and acceleration=-alpha. This is a joint command-history diagnosis, separate from the independently accepted progress-stop component.

The frozen actor reads seven c_delta columns but does not use the stored w_reference columns. It asks request=(new_initial+c_delta[tick]-accepted_c)/dt and projects through instantaneous limits. It is a position catch-up controller, not an exact replay of the old accepted velocities. Raw c debt changes from approximately -3.13e-8rad at725 to +4.72e-5 at750, -.001231 at775 and +.001193 at792. At rejection the reference velocity is0 but catch-up request is{request[3]:.9g}rad/s; jerk history still forces negative next velocity. Across accepted active cycles, recorded velocities differ from the independently recomputed command-only clipped request by at most{maxprojection:.3e}rad/s. These source/raw facts support debt-driven catch-up oscillation under jerk constraints; they do not prove a specific floating-point/solver/geometry cause for its earliest seed error.

The actual primary and fallback both report INFEASIBLE_BOUNDS. No post-rejection physical substep or accepted stop command exists; completed_stop=false. The last logged physical speed is{float(max(abs(vec(final,'v_post_')))):.9g}rad/s. Final logged command age{float(cycles[-1]['command_age_s']):.9g}s is below50ms, although the cycle misses4ms. The empty-box proof is independent of timing. Frozen model coefficients are not changed or fitted. Producer snapshots are actual captured QPs, not a reconstruction of an uncaptured matrix. Root owns backups and any future prospective continuation study; no tolerance/guard relaxation is proposed.
'''
    (args.output/'AUDIT.md').write_text(note)
    print(json.dumps({k:result[k] for k in ['verdict','axis3','first_accepted_state_outside_necessary_signed_speed_cone','max_recorded_velocity_difference_from_command_only_clamped_request_rad_s','primary_stop_shapes']},indent=2))


if __name__=='__main__':main()
