from pathlib import Path
import os,stat,re,zlib,hashlib
BLOCK=65536
RAW_CAP=128*1024**2
STORED_CAP=256*1024**2
MANIFEST_CAP=32*1024**2
CACHE_CAP=64*1024**2
_cache={};_cache_charged=0
class EvidenceError(ValueError):pass
def require(b,s):
 if not b:raise EvidenceError(s)
def bounded_read(path,cap):
 fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
 try:
  before=os.fstat(fd);require(stat.S_ISREG(before.st_mode) and before.st_size<=cap,'bounded regular file before read')
  data=bytearray()
  while True:
   b=os.read(fd,BLOCK)
   if not b:break
   require(len(b)<=cap-len(data),'bounded read before append');data.extend(b)
  after=os.fstat(fd);require((before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns) and len(data)==before.st_size,'stable full byte read');return bytes(data)
 finally:os.close(fd)
def manifest_entries(path):
 global _cache_charged
 path=Path(path);st=path.stat();identity=(st.st_ino,st.st_size,st.st_mtime_ns)
 if path in _cache:require(_cache[path][0]==identity,'manifest changed during immutable audit');return _cache[path][1]
 require(len(_cache)<512 and st.st_size<=CACHE_CAP-_cache_charged,'bounded manifest cache admission');b=bounded_read(path,MANIFEST_CAP);text=b.decode('utf-8');require(text.startswith('schema: ACTIVE_SESSION_EVIDENCE_MANIFEST_V1\n'),'fixed producer manifest schema');entries={};active=None;infiles=False;modern=False
 keys={'role','bytes','sha256','created','hash_valid','complete','error','codec','raw_bytes','raw_sha256','storage_stream_complete','raw_hash_valid','compressor_input_hash_valid','zlib_allocation_peak','raw_scope'}
 required={'bytes','sha256','created','hash_valid','complete'};newkeys={'codec','raw_bytes','raw_sha256','storage_stream_complete','raw_hash_valid','compressor_input_hash_valid','zlib_allocation_peak','raw_scope'};seen=set()
 def complete():
  if active is not None:
   require(required<=seen and (not modern or newkeys<=seen),'receipt missing required scalar/codec/raw fields')
   require(modern or not (newkeys & seen),'modern receipt fields need explicit new manifest semantics marker')
 for line in text.splitlines():
  if not infiles and line.startswith('output_bytes_semantics: '):require(line=='output_bytes_semantics: LOGICAL_RAW_CONSUMED_BINARY_EXCLUDES_MANIFEST' and not modern,'exact unique modern semantics marker');modern=True;continue
  if line=='files:':require(not infiles,'duplicate files stanza');infiles=True;continue
  if not infiles:continue
  if line.startswith('  - file: '):
   complete();name=line[len('  - file: '):];require(bool(re.fullmatch(r'[A-Za-z0-9_-]+\.bin',name)) and name not in entries and len(entries)<24,'bounded unique literal file name');active={'file':name};entries[name]=active;seen=set();continue
  require(active is not None,'receipt stanza required')
  if line.startswith('      ') or not line:continue # quoted/block text continuation only; never scalar interpretation
  match=re.fullmatch(r'    ([a-z0-9_]+): (.*)',line);require(match is not None,'fixed scalar receipt indentation required');key,value=match.groups();require(key in keys and key not in seen,'unknown/duplicate receipt key');seen.add(key)
  if key in ['bytes','raw_bytes','zlib_allocation_peak']:require(bool(re.fullmatch(r'0|[1-9][0-9]{0,18}',value)),'literal bounded unsigned scalar');active[key]=int(value)
  elif key in ['created','hash_valid','complete','storage_stream_complete','raw_hash_valid','compressor_input_hash_valid']:require(value in ['true','false'],'literal boolean scalar');active[key]=value=='true'
  elif key in ['sha256','raw_sha256']:require(value=='""' or bool(re.fullmatch('[0-9a-f]{64}',value)),'literal SHA scalar');active[key]='' if value=='""' else value
  elif key=='codec':require(value in ['RAW_V1','GZIP_DEFLATE_V1'],'known pinned codec');active[key]=value
 complete();require(infiles and entries,'nonempty receipt set');_cache_charged+=len(b);_cache[path]=(identity,entries);return entries

def verify_artifact(path,collect=False,require_source_complete=True):
 path=Path(path);entry=manifest_entries(path.parent/'MANIFEST.yaml').get(path.name);require(entry is not None,'artifact present in manifest');require(entry['created'] and entry['hash_valid'],'actual storedprefix hash available');require(not require_source_complete or entry['complete'],'source artifact incomplete, no math decode');require(entry['bytes']<=STORED_CAP,'stored file bounded before read')
 codec=entry.get('codec','RAW_V1');raw_limit=entry.get('raw_bytes',entry['bytes']);require(0<=raw_limit<=RAW_CAP,'declared logicalraw bounded before inflate');closed=entry.get('storage_stream_complete',codec=='RAW_V1');raw_valid=entry.get('raw_hash_valid',codec=='RAW_V1' and entry['hash_valid']);require(closed and raw_valid,'raw reconstruction unavailable from incomplete storedstream')
 if codec=='GZIP_DEFLATE_V1':require(entry.get('compressor_input_hash_valid') and bool(entry.get('raw_sha256')),'valid consumedinput digest required')
 storedhash=hashlib.sha256();rawhash=hashlib.sha256();seen=raw_seen=0;output=bytearray() if collect else None;decoder=zlib.decompressobj(15+16) if codec=='GZIP_DEFLATE_V1' else None
 fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
 def accept(b):
  nonlocal raw_seen
  require(len(b)<=raw_limit-raw_seen and len(b)<=RAW_CAP-raw_seen,'raw expansion cap before hashing/materialization');raw_seen+=len(b);rawhash.update(b)
  if collect:output.extend(b)
 try:
  before=os.fstat(fd);require(stat.S_ISREG(before.st_mode) and before.st_size==entry['bytes'],'regular stored size matches receipt')
  while True:
   block=os.read(fd,BLOCK)
   if not block:break
   require(len(block)<=entry['bytes']-seen,'stored byte cap before decode');seen+=len(block);storedhash.update(block)
   if decoder is None:
    require(seen!=len(block) or not block.startswith(b'\x1f\x8b'),'gzip bytes cannot be promoted to legacy RAW');accept(block);continue
   data=block
   while True:
    out=decoder.decompress(data,BLOCK);accept(out);require(not decoder.unused_data,'single gzip no trailing/concatenated members');data=decoder.unconsumed_tail
    if not data and len(out)<BLOCK:break
  if decoder is not None:require(decoder.eof and not decoder.unused_data and not decoder.unconsumed_tail,'closed gzip CRC/EOF and no trailing bytes required')
  after=os.fstat(fd);require((before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns),'immutable stored file during read');require(seen==entry['bytes'] and storedhash.hexdigest()==entry['sha256'],'full storedSHA/size exact');require(raw_seen==raw_limit and rawhash.hexdigest()==entry.get('raw_sha256',entry['sha256']),'full reconstructedraw SHA/size exact')
  facts={'file':str(path),'codec':codec,'stored_bytes':seen,'stored_sha256':storedhash.hexdigest(),'raw_bytes':raw_seen,'raw_sha256':rawhash.hexdigest(),'source_complete':entry['complete'],'closed_raw_prefix_valid':True,'scope':'source complete is separate from successful gzip prefix reconstruction; no Model/native/mathematical acceptance'}
  return (bytes(output),facts) if collect else facts
 finally:os.close(fd)
def read_artifact_bytes(path):
 path=Path(path)
 if path.suffix!='.bin':return bounded_read(path,MANIFEST_CAP)
 return verify_artifact(path,collect=True,require_source_complete=True)[0]
