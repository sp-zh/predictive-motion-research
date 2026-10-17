"""One-shot, bounded stored-evidence stream; no Model or experiment invocation.

The producer's sent receipt proves a stream was sent. Only this consumer's
persisted readback can establish a verified Mac archive. UNKNOWN native bytes
are preserved as bytes and never promoted to readable/complete codecs.
"""
from pathlib import Path
import argparse
import fcntl
import hashlib
import json
import os
import selectors
import shutil
import signal
import stat
import subprocess
import tarfile
import time
import zlib

ARCHIVE_CAP = 4 << 30
PAYLOAD_CAP = 7 << 29
TAR_CAP = 17 << 28
META_CAP = 16 << 20
RESERVE = 33 << 30
BLOCK = 65536


def digest(data):
    return hashlib.sha256(data).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def safe_name(name):
    p = Path(name)
    return bool(name) and not p.is_absolute() and '..' not in p.parts and '\x00' not in name


def metadata_write(path, data, ledger):
    path.parent.mkdir(parents=True, exist_ok=True)
    require(not path.exists(), 'metadata output already exists')
    if ledger:
        with (ledger / 'LOCK').open('a+b') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            state = json.loads((ledger / 'LEDGER.json').read_text())
            require(len(state['outputs']) < 10000, 'shared derived output count exhausted')
            require(len(data) <= state['cap'] - state['charged'], 'shared derived budget exhausted')
            state['charged'] += len(data)
            state['outputs'].append(dict(path=str(path), root=str(path.parent), bytes=len(data), sha256=digest(data), reserved_before_write=True))
            encoded = (json.dumps(state, indent=2) + '\n').encode()
            require(len(encoded) <= 8 << 20, 'ledger serialization cap')
            temporary = ledger / ('LEDGER.pending-stream-' + str(len(state['outputs'])))
            with temporary.open('xb') as out:
                out.write(encoded)
            os.replace(temporary, ledger / 'LEDGER.json')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as out:
        out.write(data)
        out.flush()
        os.fsync(out.fileno())


def write_json(path, value, ledger):
    metadata_write(path, (json.dumps(value, indent=2) + '\n').encode(), ledger)


def copy_stream(metadata, destination, report_dir, command, ledger=None, wall=1200):
    started = time.monotonic()
    require(0 < wall <= 1200, 'wall cap cannot expand')
    require(not destination.exists(), 'fresh destination required; failed parts cannot be overwritten')
    entries = {}
    paths = list(metadata.iterdir())
    require(len(paths) <= 16 and all(p.is_file() and not p.is_symlink() for p in paths), 'bounded regular metadata roster')
    require(sum(p.stat().st_size for p in paths) <= META_CAP, 'metadata pre-read aggregate cap')
    for p in paths:
        require(p.is_file() and not p.is_symlink(), 'metadata must contain regular files only')
        require(p.stat().st_size <= META_CAP, 'metadata file cap')
        entries[p.name] = p.read_bytes()
    require(sum(map(len, entries.values())) <= META_CAP, 'metadata aggregate cap')
    prepared = json.loads(entries['STREAM_PREPARED.json'])
    limits = prepared['limits']
    require(prepared['purpose'] in ['NATIVE_FINITE65', 'NATIVE_FINITE66', 'PROTOCOL_TEST_ONLY'], 'explicit archive purpose required')
    require(all(isinstance(limits[k], int) and limits[k] > 0 for k in ['archive_bytes', 'payload_bytes', 'tar_raw_bytes', 'metadata_bytes']), 'positive integer stream limits')
    require(digest(entries['strict_codec_reader.py']) == 'c32178a23e5254f44ee21a62be655af3236c708c02bb061564c3d8b0b8cb468a', 'frozen canonical reader pin')
    require(limits['archive_bytes'] <= ARCHIVE_CAP and limits['payload_bytes'] <= PAYLOAD_CAP and limits['tar_raw_bytes'] <= TAR_CAP and limits['metadata_bytes'] <= META_CAP, 'producer limits exceed agreed bounds')
    limits = dict(limits)
    if prepared['purpose'] == 'PROTOCOL_TEST_ONLY':
        require(limits['archive_bytes'] <= 8 << 20 and limits['payload_bytes'] <= 8 << 20 and limits['metadata_bytes'] <= 1 << 20, 'small protocol fixture bounds required')
        limits['tar_raw_bytes'] = min(limits['tar_raw_bytes'], 16 << 20)
    require(shutil.disk_usage(destination.parent).free >= RESERVE + limits['archive_bytes'] + limits['metadata_bytes'], 'Mac reserve plus prospective archive/metadata required')
    metadata_charged = 0

    def emit(path, data, final_failure=False):
        nonlocal metadata_charged
        reserve = 0 if final_failure else 8192
        require(len(data) <= limits['metadata_bytes'] - metadata_charged - reserve, 'aggregate metadata prewrite cap')
        metadata_charged += len(data)
        metadata_write(path, data, ledger)

    def emit_json(path, value, final_failure=False):
        emit(path, (json.dumps(value, indent=2) + '\n').encode(), final_failure)
    for name, key in [('SOURCE_MANIFEST.json', 'source_manifest'), ('FULL_NATIVE_CODEC_READBACK.json', 'codec_report')]:
        require(prepared[key] == dict(bytes=len(entries[name]), sha256=digest(entries[name])), 'prepared metadata identity mismatch')
    manifest = json.loads(entries['SOURCE_MANIFEST.json'])
    codecs = json.loads(entries['FULL_NATIVE_CODEC_READBACK.json'])
    require(manifest['native_source'] == prepared['native_source'], 'source root mismatch')
    prefix = prepared['prefix']
    require(safe_name(prefix) and prefix.endswith('/'), 'invalid native member prefix')
    expected = {}
    for e in manifest['files']:
        name = e['path']
        require(safe_name(name) and name.startswith(prefix) and name not in expected, 'invalid/duplicate payload member')
        require(0 <= e['bytes'] <= 256 << 20, 'payload per-file cap')
        expected[name] = dict(bytes=e['bytes'], sha256=e['sha256'])
    require(len(expected) == manifest['payload_count'] == prepared['payload_count'] <= 40000, 'payload count mismatch')
    payload_bytes = sum(e['bytes'] for e in expected.values())
    require(payload_bytes == manifest['payload_bytes'] == prepared['payload_bytes'] <= limits['payload_bytes'], 'payload bytes mismatch')
    members = prepared['metadata_members']
    require(isinstance(members, dict) and len(members) == 4 and all(safe_name(n) and Path(n).name == n and n in entries for n in members), 'four pinned metadata member identities required')
    require({'SOURCE_MANIFEST.json', 'FULL_NATIVE_CODEC_READBACK.json', 'strict_codec_reader.py'}.issubset(members), 'missing verification metadata')
    for name in members:
        require(name not in expected, 'metadata/payload collision')
        identity = dict(bytes=len(entries[name]), sha256=digest(entries[name]))
        require(members[name] == identity, 'declared metadata member identity mismatch: ' + name)
        expected[name] = identity
    inner = {}
    for e in codecs['files']:
        relative = Path(e['file']).relative_to(prepared['native_source'])
        name = prefix + str(relative)
        require(name in expected and name not in inner, 'codec not in manifest/duplicate codec')
        require(e['stored_bytes'] == expected[name]['bytes'] and e['stored_sha256'] == expected[name]['sha256'], 'stored codec identity mismatch')
        require(e['codec'] in ['GZIP_DEFLATE_V1', 'RAW_V1'], 'unknown storage codec')
        if not e['closed_raw_prefix_valid']:
            require(e['source_complete'] is False and e['storage_state'] == 'UNKNOWN_PREFIX' and bool(e['error']), 'uncertified bytes need explicit incomplete UNKNOWN qualification')
        else:
            require(0 <= e['raw_bytes'] <= 128 << 20 and isinstance(e['raw_sha256'], str), 'raw codec cap/identity')
        inner[name] = e
    require(set(inner) == {name for name in expected if name.endswith('.bin')}, 'every native binary needs a certified or explicit UNKNOWN record')
    report_dir.mkdir(parents=True, exist_ok=True)
    plan = dict(schema='MAC_SINGLE_DIRECT_STREAM_PLAN_V1', purpose=prepared['purpose'], prepared_sha256=digest(entries['STREAM_PREPARED.json']), archive_cap=limits['archive_bytes'], payload_cap=limits['payload_bytes'], tar_raw_cap=limits['tar_raw_bytes'], metadata_cap=limits['metadata_bytes'], Mac_reserve=RESERVE, attempts=1, wall_cap=wall, destination=str(destination), no_Dell_archive_stock=True, unknown_stored_bytes_preserved_without_raw_completion_promotion=True)
    emit_json(report_dir / 'PLAN.json', plan)
    destination.mkdir()
    part = destination / 'complete.tar.gz.part'
    final = destination / 'complete.tar.gz'
    process = None
    sink = None
    before = shutil.disk_usage(destination.parent).free
    previous_alarm = signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('finite direct-stream deadline')))
    signal.alarm(wall)
    try:
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ, 'out')
        selector.register(process.stderr, selectors.EVENT_READ, 'err')
        stderr = bytearray()
        stdout_done = False
        sink = part.open('xb')
        stored_hash = hashlib.sha256()

        def next_stored():
            nonlocal stdout_done
            while not stdout_done:
                require(time.monotonic() - started <= wall, 'stream deadline')
                for key, _ in selector.select(.25):
                    block = os.read(key.fileobj.fileno(), BLOCK)
                    if not block:
                        selector.unregister(key.fileobj)
                        if key.data == 'out':
                            stdout_done = True
                        continue
                    if key.data == 'err':
                        require(len(stderr) + len(block) <= 65536, 'producer stderr cap')
                        stderr.extend(block)
                    else:
                        return block
            return b''

        class Stream:
            def __init__(self):
                self.z = zlib.decompressobj(31)
                self.pending = b''
                self.buffer = bytearray()
                self.stored = self.raw = 0
                self.done = False

            def read(self, size):
                require(0 <= size <= 1 << 20, 'bounded tar reader request')
                while len(self.buffer) < size and not self.done:
                    if not self.pending:
                        block = next_stored()
                        if not block:
                            require(self.z.eof and not self.z.unused_data and not self.z.unconsumed_tail, 'outer gzip EOF/CRC/trailing data')
                            self.done = True
                            break
                        require(len(block) <= limits['archive_bytes'] - self.stored, 'compressed prewrite archive cap')
                        self.stored += len(block)
                        stored_hash.update(block)
                        sink.write(block)
                        self.pending = block
                    data = self.z.decompress(self.pending, BLOCK)
                    self.pending = self.z.unconsumed_tail
                    require(not self.z.unused_data and len(data) <= limits['tar_raw_bytes'] - self.raw, 'outer raw/trailing bound')
                    self.raw += len(data)
                    self.buffer.extend(data)
                    require(len(self.buffer) <= (1 << 20) + BLOCK, 'bounded raw buffer')
                data = bytes(self.buffer[:size])
                del self.buffer[:size]
                return data

        stream = Stream()
        seen = set()
        inner_seen = set()
        counts = dict(source_complete=0, closed_source_failure_prefix=0, unknown_stored_only=0, opaque_raw_only=0)
        native_raw = 0
        with tarfile.open(fileobj=stream, mode='r|') as archive:
            for member in archive:
                name = member.name
                require(member.isfile() and safe_name(name) and name in expected and name not in seen, 'unexpected/unsafe/duplicate tar member')
                require(member.size == expected[name]['bytes'], 'tar member size mismatch')
                seen.add(name)
                source = archive.extractfile(member)
                h = hashlib.sha256()
                n = 0
                e = inner.get(name)
                certified = e and e['closed_raw_prefix_valid']
                z = zlib.decompressobj(31) if certified and e['codec'] == 'GZIP_DEFLATE_V1' else None
                rh = hashlib.sha256()
                rn = 0
                while block := source.read(BLOCK):
                    require(len(block) <= member.size - n, 'member read bound')
                    n += len(block)
                    h.update(block)
                    if certified:
                        data = block
                        while True:
                            out = z.decompress(data, BLOCK) if z else data
                            require(len(out) <= e['raw_bytes'] - rn, 'inner raw prewrite bound')
                            rn += len(out)
                            rh.update(out)
                            if not z:
                                break
                            require(not z.unused_data, 'inner multiple/trailing gzip stream')
                            data = z.unconsumed_tail
                            if not data and len(out) < BLOCK:
                                break
                require(dict(bytes=n, sha256=h.hexdigest()) == expected[name], 'stored member SHA mismatch')
                if e:
                    inner_seen.add(name)
                    if certified:
                        require((not z or z.eof and not z.unused_data and not z.unconsumed_tail) and rn == e['raw_bytes'] and rh.hexdigest() == e['raw_sha256'], 'inner CRC/EOF/raw SHA mismatch')
                        native_raw += rn
                        counts['opaque_raw_only' if e.get('kind') == 'OPAQUE_NON_NATIVE_RAW_FILE' else 'source_complete' if e['source_complete'] else 'closed_source_failure_prefix'] += 1
                    else:
                        counts['unknown_stored_only'] += 1
        require(seen == set(expected) and inner_seen == set(inner), 'missing archive member/codec')
        while stream.read(BLOCK):
            pass
        sink.flush()
        os.fsync(sink.fileno())
        sink.close()
        sink = None
        while selector.get_map():
            require(time.monotonic() - started <= wall, 'receipt deadline')
            for key, _ in selector.select(.25):
                block = os.read(key.fileobj.fileno(), BLOCK)
                if not block:
                    selector.unregister(key.fileobj)
                else:
                    require(key.data == 'err' and len(stderr) + len(block) <= 65536, 'unexpected stream bytes/receipt overflow')
                    stderr.extend(block)
        require(process.wait(timeout=10) == 0, 'producer did not complete')
        sent = json.loads(stderr)
        require(sent['complete'] is True and sent['source_before_after_stable'] is True and sent['bytes'] == stream.stored and sent['sha256'] == stored_hash.hexdigest() and sent['outer_tar_raw_bytes'] == stream.raw and sent['source_manifest_sha256'] == digest(entries['SOURCE_MANIFEST.json']), 'producer sent receipt mismatch')
        h = hashlib.sha256()
        z = zlib.decompressobj(31)
        n = rn = 0
        with part.open('rb') as source:
            while block := source.read(BLOCK):
                n += len(block)
                h.update(block)
                data = block
                while True:
                    out = z.decompress(data, BLOCK)
                    rn += len(out)
                    require(rn <= limits['tar_raw_bytes'] and not z.unused_data, 'persisted raw/trailing bound')
                    data = z.unconsumed_tail
                    if not data and len(out) < BLOCK:
                        break
        require(n == stream.stored and h.hexdigest() == stored_hash.hexdigest() and rn == stream.raw and z.eof and not z.unused_data and not z.unconsumed_tail, 'persisted whole-file SHA/CRC/EOF mismatch')
        require(shutil.disk_usage(destination.parent).free >= RESERVE, 'Mac final reserve')
        report = dict(schema='MAC_DIRECT_STREAM_STORED_EVIDENCE_READBACK_V1', archive=str(final), bytes=n, sha256=h.hexdigest(), outer_tar_raw_bytes=rn, members=len(seen), payload_members=manifest['payload_count'], codec_counts=counts, certified_inner_raw_bytes=native_raw, every_stored_member_SHA_size_verified=True, certified_inner_raw_SHA_CRC_singleEOF_verified=True, UNKNOWN_inner_raw_CRC_explicitly_unverified=counts['unknown_stored_only'], Mac_persisted_full_file_reopened_SHA_CRC_verified=True, Dell_source_preserved=prepared['native_source'], independent_devices_format='Dell original frozen files and Mac complete tar; no Dell second tar file', producer_sent_receipt=sent, Mac_free_before=before, Mac_free_after=shutil.disk_usage(destination.parent).free, wall_seconds=time.monotonic() - started, scope='Complete stored-byte recovery only. Closed source-failure/UNKNOWN bytes retain original qualification. Not standalone environment, mathematical/physical stop, realtime, task or phase acceptance.')
        emit_json(report_dir / 'FULL_READBACK.json', report)
        part.chmod(0o444)
        os.rename(part, final)
        for name in members:
            emit(destination / name, entries[name])
        emit(destination / 'PRODUCER_PREPARED.json', entries['STREAM_PREPARED.json'])
        emit_json(destination / 'PRODUCER_SENT.json', sent)
        emit(destination / 'ROOT_FULL_READBACK.json', (report_dir / 'FULL_READBACK.json').read_bytes())
        meta_bytes = sum(p.stat().st_size for p in destination.iterdir() if p != final)
        require(meta_bytes + 8192 <= META_CAP, 'final metadata aggregate bound')
        ready = dict(schema='MAC_DIRECT_STREAM_PERSISTED_ARCHIVE_READY_V1', archive=str(final), bytes=n, sha256=h.hexdigest(), members=len(seen), codec_counts=counts, producer_sent_is_not_Mac_readback=True, persisted_readback_passed=True, no_Dell_duplicate_archive_stock=True, full_readback_sha256=digest((report_dir / 'FULL_READBACK.json').read_bytes()), scope=report['scope'])
        emit_json(destination / 'READY.json', ready)
        for p in destination.iterdir():
            p.chmod(0o444)
        fd = os.open(destination, os.O_RDONLY | os.O_DIRECTORY)
        os.fsync(fd)
        os.close(fd)
        destination.chmod(0o555)
        return ready
    except BaseException as error:
        if sink:
            sink.close()
        if process and process.poll() is None:
            process.kill()
            process.wait()
        emit_json(report_dir / 'FAILURE.json', dict(error=repr(error), any_part_preserved=True, no_retry_no_reset_no_refund=True, no_confirmed_READY_claim=True, READY_file_exists_but_unconfirmed=(destination / 'READY.json').exists(), scope='The one-shot attempt failed; preserve bytes and original producer source. No experiment/native counters changed.'), final_failure=True)
        raise
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous_alarm)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--metadata-dir', type=Path, required=True)
    p.add_argument('--destination', type=Path, required=True)
    p.add_argument('--report-dir', type=Path, required=True)
    p.add_argument('--command-json', type=Path, required=True)
    p.add_argument('--budget-ledger', type=Path)
    p.add_argument('--wall', type=int, default=1200)
    a = p.parse_args()
    command = json.loads(a.command_json.read_text())
    require(isinstance(command, list) and command and all(isinstance(x, str) for x in command), 'explicit argv list required; no shell interpolation')
    print(json.dumps(copy_stream(a.metadata_dir, a.destination, a.report_dir, command, a.budget_ledger, a.wall)))


if __name__ == '__main__':
    main()
