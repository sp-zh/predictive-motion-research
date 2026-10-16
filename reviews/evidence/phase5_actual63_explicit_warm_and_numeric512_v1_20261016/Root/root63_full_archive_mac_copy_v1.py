from pathlib import Path
import sys, os, json, hashlib, subprocess, shlex, zlib, tarfile, io, time, signal, shutil, stat, ast, fcntl
sys.dont_write_bytecode = True
sys.path.insert(0, '/private/tmp')
from bounded_derived_bytes53_v1 import bounded_write
R = Path('/Users/uot/Documents/ChatGPT/ros')
O = Path('/private/tmp/root63_review_v1_20261016')
os.environ['P5_DERIVED53_ROOT'] = str(O)
M = Path('/private/tmp/phase5_current_braking_nominal63_source_v1_20261016/full_archive63_v2/readback')
D = R / 'transfer/cold-backups/native63-complete-20261016-v2'
CAP = 4 * 1024 ** 3
META = 16 * 1024 ** 2
RESERVE = 33 * 1024 ** 3
START = time.monotonic()
BLOCK = 65536

def sha(b):
    return hashlib.sha256(b).hexdigest()
ready = json.loads((M / 'READY.json').read_text())
manifest = json.loads((M / 'SOURCE_MANIFEST.json').read_text())
codecs = json.loads((M / 'FULL_NATIVE_CODEC_READBACK.json').read_text())
assert sha((M / 'READY.json').read_bytes()) == 'dfa2bb34d71af59d3fe4a0eb23d81cade345bb3265f73834348c84709ebf4bc4' and ready['sha256'] == '387b5ac46e9667c75aa670072177b8522529a2300b90ddd6113c174ebeeba2bd' and (ready['bytes'] == 2068830601)
assert ready['archive_path'] == '/home/codextransfer/predictive_motion/transfer/cold-archives/native63-complete-20261016-v2/complete63.tar.gz'
assert 0 < ready['bytes'] <= CAP and ready['source_manifest'] == dict(bytes=(M / 'SOURCE_MANIFEST.json').stat().st_size, sha256=sha((M / 'SOURCE_MANIFEST.json').read_bytes())) and (ready['codec_report'] == dict(bytes=(M / 'FULL_NATIVE_CODEC_READBACK.json').stat().st_size, sha256=sha((M / 'FULL_NATIVE_CODEC_READBACK.json').read_bytes())))
receipt = json.loads((M / 'METADATA_RECEIPT.json').read_text())
for e in receipt:
    b = (M / e['path']).read_bytes()
    assert len(b) == e['bytes'] and sha(b) == e['sha256']
assert manifest['payload_count'] == 3247 and manifest['payload_bytes'] == 2122700033 and len(codecs['files']) == 2339 and ready['members_verified'] == 3252
assert ready['archive_aggregate_current_bytes'] == 4137652196 <= ready['archive_aggregate_cap'] == 9663676416
assert not D.exists() and shutil.disk_usage(R).free >= RESERVE and ready['full_gzip_crc_singleEOF_no_trailing']
expected = {x['path']: dict(bytes=x['bytes'], sha256=x['sha256']) for x in manifest['files']}
assert len(expected) == manifest['payload_count'] <= 40000 and sum((x['bytes'] for x in expected.values())) == manifest['payload_bytes'] <= 8 * 1024 ** 3
for name in ['SOURCE_MANIFEST.json', 'FULL_NATIVE_CODEC_READBACK.json', 'archive63_complete_producer_v3.py', 'strict_codec_reader.py', 'PRESERVED_ARCHIVE_V1_FAILURE.json']:
    b = (M / name).read_bytes()
    expected[name] = dict(bytes=len(b), sha256=sha(b))
inner = {}
for e in codecs['files']:
    n = 'native63/' + str(Path(e['file']).relative_to(manifest['native_source']))
    assert n in expected and n not in inner and e['source_complete'] and e['closed_raw_prefix_valid']
    assert {k: e[k] for k in ['stored_bytes', 'stored_sha256']} == dict(stored_bytes=expected[n]['bytes'], stored_sha256=expected[n]['sha256'])
    inner[n] = e
before = shutil.disk_usage(R).free
plan = dict(schema='ROOT63_POST_NATIVE_SINGLE_MAC_ARCHIVE_COPY_PLAN_V1', archive=ready['archive_path'], sha256=ready['sha256'], actual_bytes=ready['bytes'], single_part_or_final_cap=CAP, metadata_cap=META, minimum_free_before_after=RESERVE, Mac_destination=str(D), attempts=1, no_expanded_native_mirror=True, original_inrun12GiB_and_selected_caps_unchanged=True, scope='Separate authorized post-native milestone backup. Preserve Dell original and any failed Mac part; no reset/refund/cleanup or native execution. Does not close older replication gaps or environment restoration.')
bounded_write(O / 'POST_NATIVE_MAC_BACKUP_PLAN.json', json.dumps(plan, indent=2) + '\n')
D.mkdir()
part = D / 'complete63.tar.gz.part'
final = D / 'complete63.tar.gz'
signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('finite120s archive stream/copy/readback timeout')))
signal.alarm(120)
code = "from pathlib import Path\nimport os,sys,json,stat\np=Path(ARCHIVE);fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW);a=os.fstat(fd);assert stat.S_ISREG(a.st_mode)and a.st_size==SIZE\nwhile True:\n b=os.read(fd,65536)\n if not b:break\n sys.stdout.buffer.write(b)\nsys.stdout.buffer.flush();z=os.fstat(fd);os.close(fd);assert(a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_ino,z.st_size,z.st_mtime_ns);sys.stderr.write(json.dumps({'fd_identity_stable':True,'bytes':z.st_size,'mode':stat.S_IMODE(z.st_mode)}))".replace('ARCHIVE', repr(ready['archive_path'])).replace('SIZE', str(ready['bytes']))
proc = None
try:
    proc = subprocess.Popen(['tools/dell-ssh.sh', '-T', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=8', 'DellTransfer', 'python3 -I -S -B -c ' + shlex.quote(code)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=R)
    sink = part.open('xb')
    outerhash = hashlib.sha256()

    class Stream:

        def __init__(self):
            self.z = zlib.decompressobj(31)
            self.pending = b''
            self.buffer = bytearray()
            self.stored = self.raw = 0
            self.done = False

        def read(self, n):
            assert 0 <= n <= 1024 ** 2
            while len(self.buffer) < n and (not self.done):
                if not self.pending:
                    b = proc.stdout.read(BLOCK)
                    if not b:
                        assert self.z.eof and (not self.z.unused_data) and (not self.z.unconsumed_tail)
                        self.done = True
                        break
                    assert len(b) <= ready['bytes'] - self.stored and len(b) <= CAP - self.stored
                    self.stored += len(b)
                    outerhash.update(b)
                    sink.write(b)
                    self.pending = b
                out = self.z.decompress(self.pending, BLOCK)
                self.pending = self.z.unconsumed_tail
                assert not self.z.unused_data and len(out) <= ready['outer_tar_raw_bytes'] - self.raw
                self.raw += len(out)
                self.buffer.extend(out)
                assert len(self.buffer) <= 1024 ** 2 + BLOCK
            b = bytes(self.buffer[:n])
            del self.buffer[:n]
            return b
    stream = Stream()
    seen = set()
    native_seen = set()
    native_raw = 0
    member_bytes = 0
    with tarfile.open(fileobj=stream, mode='r|') as tar:
        for member in tar:
            name = member.name
            assert member.isfile() and (not name.startswith('/')) and ('..' not in Path(name).parts) and (name in expected) and (name not in seen) and (member.size == expected[name]['bytes']) and (member.size <= 256 * 1024 ** 2)
            seen.add(name)
            h = hashlib.sha256()
            n = 0
            source = tar.extractfile(member)
            e = inner.get(name)
            z = zlib.decompressobj(31) if e and e['codec'] == 'GZIP_DEFLATE_V1' else None
            rh = hashlib.sha256()
            rn = 0
            while (b := source.read(BLOCK)):
                assert len(b) <= member.size - n
                n += len(b)
                h.update(b)
                if e:
                    data = b
                    while True:
                        out = z.decompress(data, BLOCK) if z else data
                        assert len(out) <= e['raw_bytes'] - rn and len(out) <= 128 * 1024 ** 2 - rn
                        rn += len(out)
                        rh.update(out)
                        if not z:
                            break
                        assert not z.unused_data
                        data = z.unconsumed_tail
                        if not data and len(out) < BLOCK:
                            break
            assert dict(bytes=n, sha256=h.hexdigest()) == expected[name]
            member_bytes += n
            if e:
                assert (not z or (z.eof and (not z.unused_data) and (not z.unconsumed_tail))) and rn == e['raw_bytes'] and (rh.hexdigest() == e['raw_sha256'])
                native_seen.add(name)
                native_raw += rn
    assert seen == set(expected) and native_seen == set(inner)
    while stream.read(BLOCK):
        pass
    assert stream.stored == ready['bytes'] and outerhash.hexdigest() == ready['sha256'] and (stream.raw == ready['outer_tar_raw_bytes'])
    sink.flush()
    os.fsync(sink.fileno())
    sink.close()
    stderr = proc.stderr.read(16385)
    assert len(stderr) <= 16384 and proc.wait(timeout=10) == 0
    remote_fd = json.loads(stderr)
    assert remote_fd['fd_identity_stable']
    h = hashlib.sha256()
    z = zlib.decompressobj(31)
    n = rn = 0
    with part.open('rb') as f:
        while (b := f.read(BLOCK)):
            n += len(b)
            h.update(b)
            data = b
            while True:
                out = z.decompress(data, BLOCK)
                rn += len(out)
                assert rn <= ready['outer_tar_raw_bytes'] and (not z.unused_data)
                data = z.unconsumed_tail
                if not data and len(out) < BLOCK:
                    break
    assert n == ready['bytes'] and h.hexdigest() == ready['sha256'] and (rn == ready['outer_tar_raw_bytes']) and z.eof and (not z.unused_data) and (not z.unconsumed_tail) and (not final.exists())
    part.chmod(292)
    os.rename(part, final)
    fd = os.open(D, os.O_RDONLY | os.O_DIRECTORY)
    os.fsync(fd)
    os.close(fd)
    after = shutil.disk_usage(R).free
    assert after >= RESERVE
    report = dict(schema='ROOT63_COMPLETE_STORED_EVIDENCE_ARCHIVE_FULL_MAC_RESTORATION_AND_DISK_COPY_V1', Dell_archive=ready['archive_path'], Mac_archive=str(final), archive_bytes=n, archive_sha256=h.hexdigest(), all_members_SHA_size_restoration_verified=True, members=len(seen), payload_members=manifest['payload_count'], total_member_bytes=member_bytes, native_complete_codecs=len(native_seen), native_raw_bytes=native_raw, outer_tar_raw_bytes=rn, full_outer_and_inner_CRC_singleEOF=True, Mac_persisted_whole_file_reopened_SHA_and_CRC_verified=True, source_files_included=94, profile_and_active_ELF_included=True, dependency_build_caches_excluded=True, remote_fd_identity=remote_fd, Mac_free_before=before, Mac_free_after=after, postrun_archive_cap=CAP, metadata_cap=META, minimum33GiB_before_after_passed=True, wall_seconds=time.monotonic() - START, scope='Two independent physical Mac/Dell archive copies of complete63 stored evidence and frozen94 source/profile/active ELF. Preserved failed Dell archivev1 remains charged to original9GiB aggregate, v2 no refund. Not standalone environment restoration or mathematics/task/stop/phase acceptance. Online63 completes63 commands and fails numeric512 hint at63 before nativeSOLVED/B/C. Older replication gaps remain; original run/capture limits untouched.')
    bounded_write(O / 'FULL_ARCHIVE_MAC_READBACK_AND_COPY.json', json.dumps(report, indent=2) + '\n')
    L = Path('/private/tmp/phase5_stop53_combined_derived_budget_v1_20261015')
    new = []
    tree = ast.parse(Path('/private/tmp/root58_finish_checkpoint_v1.py').read_text())
    exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == 'copy'], type_ignores=[]), '<budgeted-copy-only>', 'exec'))
    for source, target in [(M / 'READY.json', 'DELL_READY.json'), (M / 'SOURCE_MANIFEST.json', 'SOURCE_MANIFEST.json'), (M / 'FULL_NATIVE_CODEC_READBACK.json', 'FULL_NATIVE_CODEC_READBACK.json'), (M / 'archive63_complete_producer_v3.py', 'archive63_complete_producer_v3.py'), (M / 'strict_codec_reader.py', 'strict_codec_reader.py'), (M / 'PRESERVED_ARCHIVE_V1_FAILURE.json', 'PRESERVED_ARCHIVE_V1_FAILURE.json'), (O / 'POST_NATIVE_MAC_BACKUP_PLAN.json', 'POST_NATIVE_MAC_BACKUP_PLAN.json'), (O / 'FULL_ARCHIVE_MAC_READBACK_AND_COPY.json', 'ROOT_FULL_READBACK.json')]:
        copy(source, D / target)
    meta_bytes = sum((p.stat().st_size for p in D.iterdir() if p.is_file() and p != final))
    assert meta_bytes + 8192 <= META
    mac_ready = dict(schema='MAC_AND_DELL63_COMPLETE_STORED_EVIDENCE_ARCHIVE_READBACK_READY_V1', archive=str(final), bytes=n, sha256=h.hexdigest(), Dell_archive=ready['archive_path'], all_members_verified=len(seen), all_complete_native_codecs_verified=len(native_seen), Mac_persisted_whole_readback_passed=True, two_independent_physical_archive_files_verified=True, Dell_original_READY_sha256=sha((M / 'READY.json').read_bytes()), old_Dell_PENDING_preserved=True, Root_report_sha256=sha((O / 'FULL_ARCHIVE_MAC_READBACK_AND_COPY.json').read_bytes()), metadata_bytes_before_READY=meta_bytes, scope=report['scope'])
    bounded_write(O / 'MAC_ARCHIVE_READY.json', json.dumps(mac_ready, indent=2) + '\n')
    copy(O / 'MAC_ARCHIVE_READY.json', D / 'READY.json')
    for p in D.iterdir():
        p.chmod(292)
    D.chmod(365)
    fd = os.open(D, os.O_RDONLY | os.O_DIRECTORY)
    os.fsync(fd)
    os.close(fd)
    signal.alarm(0)
    print(json.dumps(dict(archive_bytes=n, archive_sha256=h.hexdigest(), members=len(seen), inner_complete=len(native_seen), inner_raw_bytes=native_raw, Mac_READY_sha256=sha((D / 'READY.json').read_bytes()), wall_seconds=time.monotonic() - START)))
except BaseException as e:
    if proc and proc.poll() is None:
        proc.kill()
        proc.wait()
    try:
        bounded_write(O / 'FULL_ARCHIVE_MAC_COPY_FAILURE.json', json.dumps(dict(error=repr(e), partial_preserved=True, no_retry_or_reset=True), indent=2) + '\n')
    except BaseException:
        pass
    raise
