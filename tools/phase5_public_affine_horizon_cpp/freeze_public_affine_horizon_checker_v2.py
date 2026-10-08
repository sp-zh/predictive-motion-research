#!/usr/bin/env python3
"""SOURCE ONLY pending review: freeze saved affine algebra verification inputs.

No kernel, checker, matrix, model, compiler, network or plant execution. Original
d3d4/8694 and all their immutable evidence remain unchanged. New output uses the
root audit's files[{path,sha256,bytes,immutable_copy}] schema explicitly.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
from pathlib import Path

ROOT=Path('/home/codextransfer/predictive_motion')
SRC=ROOT/'tools/phase5_public_affine_horizon_cpp'
OLD_BASE=ROOT/'results/phase5/development/public-affine-horizon-cpp-v1'
AUDIT=Path('/home/codextransfer/clean-audits/root-affine-horizon-20261008')
OLD_FREEZE=OLD_BASE/'frozen_before_predictions.json'
BINARY=ROOT/'build-public-affine-horizon-cpp-v1-attempt2/public_affine_horizon_probe'
OLD_FREEZE_SHA='d3d4253c0173aae4ad3072eea37268713bd3710b68cfa05720e79f906bf97429'
OLD_CHECKER_SHA='8694688fc94eaacbdab72b64658b3c8f46ed51e90329cfbd38a8536c1f03baa6'
NEW_CHECKER_SHA='12f0df058083fb751e4a3ea0f5600e418900f42fe46939b3c15f97c18a6acc3d'
BINARY_SHA='6d08f9d00ccc939770efc9bd0c704745eba972a80f2511e0441691761eff7b4d'
PRODUCER_READY_SHA='8b7f0a0278f2bb95dfcd767f837175fbcda847069de7f17ae887ad82fbd16ce6'
ROOT_READY_SHA='693dacaeb450b602096dd40324cfc0975b0ee2da47f1f6e8305960bea5cacb1b'
SCOPE_KEYS=('connecting_segment','ball','admissibility','execution','safety',
            'uniform_error_bound','controller_readiness')


def need(condition,message):
    if not condition:raise ValueError(message)


def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1<<20),b''):digest.update(block)
    return digest.hexdigest()


def load(path):
    def pairs(items):
        out={}
        for k,v in items:
            need(k not in out,'duplicate JSON key '+k);out[k]=v
        return out
    def nonfinite(value):raise ValueError('nonfinite JSON '+value)
    return json.loads(Path(path).read_text(),object_pairs_hook=pairs,parse_constant=nonfinite)


def write(path,value):
    with Path(path).open('x') as stream:
        json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--source-checkpoint',required=True)
    parser.add_argument('--self-sha',required=True)
    parser.add_argument('--checker-review',type=Path,required=True)
    parser.add_argument('--checker-review-sha',required=True)
    parser.add_argument('--state-sha',required=True)
    parser.add_argument('--agents-sha',required=True)
    parser.add_argument('--additional-pinned',nargs=2,action='append',default=[],
                        metavar=('ABSOLUTE_PATH','SHA256'))
    args=parser.parse_args()
    need(re.fullmatch(r'[0-9a-f]{40}',args.source_checkpoint) is not None,'checkpoint SHA shape')
    for digest in (args.self_sha,args.checker_review_sha,args.state_sha,args.agents_sha):
        need(re.fullmatch(r'[0-9a-f]{64}',digest) is not None,'pinned SHA256 shape')
    out=args.output.absolute();out.mkdir(parents=True,exist_ok=False)
    try:
        need(sha(Path(__file__))==args.self_sha,'reviewed freezer source identity')
        need(sha(OLD_FREEZE)==OLD_FREEZE_SHA,'old freeze retained')
        old=load(OLD_FREEZE)
        need(old['dependency_count']==2912 and len(old['dependencies'])==2912,'old2912 exact roster')
        need(old['nonempty_calls']==0 and old['binary_sha256']==BINARY_SHA,'old scope/binary identity')
        need(sha(SRC/'verify_public_affine_horizon.py')==OLD_CHECKER_SHA,'old checker retained')
        need(sha(SRC/'verify_public_affine_horizon_v2.py')==NEW_CHECKER_SHA,'reviewed versioned checker')
        need(sha(BINARY)==BINARY_SHA,'unchanged compiled binary')
        state_path=ROOT/'PROJECT_PAUSED.json';agents_path=ROOT/'AGENTS.md'
        need(sha(state_path)==args.state_sha and sha(agents_path)==args.agents_sha,'reviewed resumption metadata')
        state=load(state_path)
        need(state['status']=='RESUMED_BY_USER' and state['continued_work_authorized'] is True,'explicit resumption required')
        need(state['phase5']=='NOT_ACCEPTED' and state['phase6']=='NOT_STARTED','no phase gate promotion')
        need(args.checker_review.is_absolute() and sha(args.checker_review)==args.checker_review_sha,'checker review identity')
        review=load(args.checker_review)
        need(review['decision']=='PASS_SOURCE_ONLY_VERSIONED_CHECKER_NEGATIVE_CONTROLS' and
             review['new_checker_sha256']==NEW_CHECKER_SHA and review['old_freeze_preserved']==OLD_FREEZE_SHA,
             'bounded source-only review prerequisite')
        need(review['nonempty_calls']==0 and review['phase5']=='NOT_ACCEPTED','no claimed numerical acceptance')

        # All old live originals AND content-addressed cached copies must match.
        # Retaining old cache alone does not conceal a changed execution source.
        sources={}
        def add(path,digest=None,size=None,category='additional'):
            path=Path(path)
            need(path.is_absolute() and path.is_file(),'regular absolute source '+str(path))
            current=sha(path);length=path.stat().st_size
            if digest is not None:need(current==digest,'source hash mismatch '+str(path))
            if size is not None:need(length==size,'source byte mismatch '+str(path))
            key=str(path)
            if key in sources:
                need(sources[key]['sha256']==current and sources[key]['bytes']==length,'conflicting source identity')
            else:sources[key]=dict(path=key,sha256=current,bytes=length,category=category)
        legacy_paths=set()
        for entry in old['dependencies']:
            need(entry['path'] not in legacy_paths,'duplicate legacy source path')
            legacy_paths.add(entry['path'])
            relative=Path(entry['cache'])
            need(not relative.is_absolute() and '..' not in relative.parts,'legacy cache traversal')
            cache=OLD_BASE/relative
            need(cache.is_file() and cache.stat().st_size==entry['bytes'] and sha(cache)==entry['sha256'],
                 'legacy immutable cache mismatch '+entry['path'])
            add(entry['path'],entry['sha256'],entry['bytes'],'legacy2912')

        add(OLD_FREEZE,OLD_FREEZE_SHA,category='legacy_freeze_identity')
        add(SRC/'verify_public_affine_horizon.py',OLD_CHECKER_SHA,category='retained_checker')
        add(SRC/'verify_public_affine_horizon_v2.py',NEW_CHECKER_SHA,category='reviewed_checker_v2')
        add(Path(__file__).absolute(),args.self_sha,category='reviewed_new_freezer')
        add(args.checker_review,args.checker_review_sha,category='checker_source_review')
        add(state_path,args.state_sha,category='human_resumption')
        add(agents_path,args.agents_sha,category='project_instructions')
        for path,digest in args.additional_pinned:
            need(re.fullmatch(r'[0-9a-f]{64}',digest) is not None,'additional pinned SHA shape')
            add(Path(path),digest,category='reviewed_additional_metadata')

        # These original prepared bytes, helper/audit and policy gates do not change.
        producer=OLD_BASE/'prepared-inputs'
        root_prepared=AUDIT/'prepared-v1'
        for directory,manifest_name,manifest_sha in (
                (producer,'INPUT_MANIFEST.json',PRODUCER_READY_SHA),
                (root_prepared,'READY.json',ROOT_READY_SHA)):
            manifest_path=directory/manifest_name
            need(sha(manifest_path)==manifest_sha,'unchanged prepared manifest '+str(manifest_path))
            ready=load(manifest_path);add(manifest_path,manifest_sha,category='prepared_manifest')
            for name,entry in ready['files'].items():
                relative=Path(name)
                need(not relative.is_absolute() and '..' not in relative.parts,'prepared traversal')
                add(directory/relative,entry['sha256'],entry['bytes'],'unchanged_prepared_input')
        for filename in ('audit_public_affine_horizon_root.py','public_affine_horizon_root_reference.py',
                         'prepare_public_affine_horizon_root.py','PREPARATION_EXECUTION.json',
                         'public_affine_horizon_root_plan_20261008.json','archived_sources.json','SOURCE_READY.json'):
            path=AUDIT/filename
            need(str(path) in sources,'root helper/preparation/source not retained in legacy closure '+filename)
        for path in (BINARY,root_prepared/'inputs.json',root_prepared/'policy.json',
                     root_prepared/'archived_sources.json'):
            need(str(path) in sources,'root audit execution path absent '+str(path))

        # Fresh immutable copies; old output/cache trees are never overwritten.
        cache_dir=out/'immutable_files';cache_dir.mkdir()
        files=[]
        for key in sorted(sources):
            entry=sources[key];source=Path(key);cache=cache_dir/entry['sha256']
            need(sha(source)==entry['sha256'],'source changed before snapshot '+key)
            if not cache.exists():
                with source.open('rb') as src,cache.open('xb') as dest:shutil.copyfileobj(src,dest,1<<20)
                os.chmod(cache,0o444)
            need(cache.stat().st_size==entry['bytes'] and sha(cache)==entry['sha256'],'new immutable copy mismatch')
            need(sha(source)==entry['sha256'],'source changed during snapshot '+key)
            files.append(dict(path=key,sha256=entry['sha256'],bytes=entry['bytes'],
                              immutable_copy=str(cache.absolute()),category=entry['category']))
        record=dict(schema_version=2,scope='FROZEN_AFFINE_ALGEBRA_VERIFICATION_SOURCES_NO_NUMERICAL_RELEASE',
                    prerequisite_private_source_checkpoint=args.source_checkpoint,
                    old_freeze_path=str(OLD_FREEZE),old_freeze_sha256=OLD_FREEZE_SHA,
                    old_checker_sha256=OLD_CHECKER_SHA,new_checker_sha256=NEW_CHECKER_SHA,
                    binary=str(BINARY),binary_sha256=BINARY_SHA,legacy_dependency_count=2912,
                    files=files,file_count=len(files),producer_manifest_sha256=PRODUCER_READY_SHA,
                    root_prepared_ready_sha256=ROOT_READY_SHA,nonempty_calls=0,
                    scope_flags=dict.fromkeys(SCOPE_KEYS,False),phase5='NOT_ACCEPTED',phase6='NOT_STARTED',
                    run_release='NOT_GRANTED_REQUIRES_INDEPENDENT_FREEZE_REVIEW_AND_BACKUP',
                    numerical_policy='unchanged prepared inputs/reference/tolerances and binary',
                    earlier_fd_failure='RETAINED_IMMUTABLE')
        freeze=out/'frozen_before_predictions_v2.json';write(freeze,record)
        for entry in files:
            need(sha(Path(entry['path']))==entry['sha256'] and
                 sha(Path(entry['immutable_copy']))==entry['sha256'],'final live/cache closure verification')
        need(sha(OLD_FREEZE)==OLD_FREEZE_SHA and sha(SRC/'verify_public_affine_horizon.py')==OLD_CHECKER_SHA,
             'legacy freeze/checker remained unchanged')
        ready=dict(freeze_path=str(freeze),freeze_sha256=sha(freeze),file_count=len(files),
                   all_live_and_immutable_copies_verified=True,legacy2912_preserved=True,
                   binary_sha256=BINARY_SHA,checker_v2_sha256=NEW_CHECKER_SHA,nonempty_calls=0,
                   run_release='NOT_GRANTED',requires_private_checkpoint_backup_and_root_review=True)
        write(out/'FREEZE_READY.json',ready)
        print(json.dumps(ready),flush=True)
    except BaseException as error:
        write(out/'FAILED_FREEZE_ATTEMPT.json',dict(error_type=type(error).__name__,error=str(error),
              scope='PRESERVED_FREEZE_FAILURE_NO_NUMERICAL_CALLS',nonempty_calls=0))
        raise


if __name__=='__main__':main()
