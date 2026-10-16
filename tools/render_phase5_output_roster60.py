"""Saved artifact-count evidence only; no controller, Model or native execution."""
from pathlib import Path
import io,json,hashlib,os,csv
def render(root):
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 from matplotlib.patches import Patch
 sources={
  'actual59_result':root/'reviews/evidence/phase5_actual59_artifact_roster_failure_v1_20261016/Root/RESULT.json',
  'actual59_roster':root/'reviews/evidence/phase5_actual59_artifact_roster_failure_v1_20261016/Root/TRIAL0_ARTIFACT_ROSTER.json',
  'pure60_review':Path('/private/tmp/root60_merged_review_v1_20261016/PURE24_MERGED_AND_FULL_ROSTER_REVIEW.json'),
  'actual58_ordered_roster_binding':Path('/private/tmp/phase5_merged_hint_diagnostics60_source_v2_20261016/FROZEN_SUCCESSFUL24_ROSTER_BINDING.json')}
 data={k:json.loads(p.read_text())for k,p in sources.items()};a=data['actual59_result'];names=data['actual59_roster'];p=data['pure60_review']
 assert a['trial_manifest_complete_files']==24 and a['missing_25th']=='cycle_timing.bin'and a['task_halves']==2 and a['entry']['commits']==1
 assert len(names)==24 and 'hint_kkt_rank_events.bin'in names and 'hint_negative_leaving_events.bin'in names and 'cycle_timing.bin'not in names
 assert p['all24_ordered_files_complete_SHA_CRC_EOF']and p['last_cycle_timing_retained']and p['expected_25th_separate_file_absent']
 assert len(data['actual58_ordered_roster_binding']['ordered_binary_names'])==24
 rows=[['actual59_native_prefix',22,1,1,0,1,24],['pure60_synthetic_output_chain',23,0,0,1,0,24]]
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
 fig,ax=plt.subplots(figsize=(11,4.8));colors=['#8D9AA8','#D7902D','#E4BA54','#2C6FA8','#C63D4B'];labels=['Other written slots','Rank V1 (59)','Chosen V1 (59)','Merged V2 (pure60)','Refused output']
 for row,y in zip(rows,[1,.12]):
  start=0
  for value,color in zip(row[1:6],colors):
   if value:ax.barh(y,value,left=start,height=.34,color=color,edgecolor='white',linewidth=1)
   start+=value
  ax.text(11,y,'24 files written',ha='center',va='center',fontsize=10,color='white',weight='bold')
 ax.axvline(24,color='#333333',linestyle='--',linewidth=1.2)
 ax.text(24,1.56,'Original limit: 24',ha='right',va='bottom',fontsize=9)
 ax.annotate('25th: cycle timing refused',xy=(24.5,1.16),xytext=(23.2,1.30),ha='right',fontsize=9,color=colors[-1],arrowprops={'arrowstyle':'-','color':colors[-1]})
 ax.text(23.8,-.15,'Final cycle timing included',ha='right',va='center',fontsize=9,color=colors[3])
 ax.set_yticks([1,.12],['Attempt 59\nnative prefix','Attempt 60\npure output test']);ax.set_ylim(-.3,1.9);ax.set_xlim(0,27);ax.set_xticks([0,8,16,24,25]);ax.set_xlabel('Binary output slots (refused slot shown)');ax.grid(axis='x',alpha=.16);ax.set_axisbelow(True)
 fig.suptitle('Evidence file count: attempt 59 failure and attempt 60 pure test',x=.04,ha='left',fontsize=15)
 fig.text(.04,.87,'The original 24-file bound is unchanged; merged V2 retains all rank and chosen-leaving records.',fontsize=9)
 fig.legend(handles=[Patch(facecolor=c,label=l)for c,l in zip(colors,labels)],loc='lower left',bbox_to_anchor=(.035,.12),ncol=3,frameon=False,fontsize=8)
 fig.text(.04,.055,'Actual59 completed 1 command / two 2 ms task halves before this output failure. Pure60 slots are dummy data.\nThis figure establishes output-count integration only: no new Model/C execution, successful stop, full task or phase acceptance.',fontsize=8.5)
 fig.subplots_adjust(left=.19,right=.96,top=.78,bottom=.30)
 out={};buffer=io.StringIO();writer=csv.writer(buffer,lineterminator='\n');writer.writerow(['case','other_written','rank_v1_written','chosen_v1_written','merged_v2_written','refused','original_limit']);writer.writerows(rows);out['csv']=buffer.getvalue().encode()
 for ext in ['png','svg']:
  b=io.BytesIO();fig.savefig(b,format=ext,dpi=180,facecolor='white');out[ext]=b.getvalue()
 plt.close(fig)
 provenance=dict(schema='ACTUAL59_AND_PURE60_FILE_COUNT_FIGURE_V1',source_pins={k:dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())for k,p in sources.items()},renderer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),matplotlib=matplotlib.__version__,original_file_limit=24,selection='All written native59 trial0 binary slots plus the explicitly missing25th; complete24-name pure60 synthetic output roster. No extrapolation to runtime60.',scope='Evidence/output integration counts only. Gray other-slot counts differ because actual59 lacks final cycle timing while pure60 includes it. Not a controller performance result.',outputs={k:dict(bytes=len(v),sha256=hashlib.sha256(v).hexdigest())for k,v in out.items()})
 out['json']=(json.dumps(provenance,indent=2)+'\n').encode();return out
if __name__=='__main__':
 import sys
 root=Path('/Users/uot/Documents/ChatGPT/ros');out=Path('/private/tmp/root60_merged_review_v1_20261016');os.environ['P5_DERIVED53_ROOT']=str(out);sys.path.insert(0,'/private/tmp')
 from bounded_derived_bytes53_v1 import bounded_write_bytes
 for ext,b in render(root).items():bounded_write_bytes(out/('output_roster59_60_v2.'+ext),b)
