from pathlib import Path
import os,sys,json,hashlib,io,csv
sys.path.insert(0,'/private/tmp');from bounded_derived_bytes53_v1 import bounded_write_bytes
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
O=Path('/private/tmp/root62_stop_cause_review_v1_20261016');os.environ['P5_DERIVED53_ROOT']=str(O)
files=[O/'SAVED61_FIRST_CONTROL_DIRECTION_RESTRICTION.json',O/'SAVED61_FORECAST_STOP_DIAGNOSTIC.json'];pins=[dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())for p in files]
e=next(x for x in json.loads(files[0].read_text())['cases']if x['case']=='cycle-43/trial-1');f=json.loads(files[1].read_text())['cases'];assert len(f)==4
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,(left,right)=plt.subplots(1,2,figsize=(12.6,5),gridspec_kw={'width_ratios':[1.3,1]});table=io.StringIO();writer=csv.writer(table);writer.writerow(['kind','case_or_joint','lower','selected','upper','units'])
for i in range(7):
 sign=1 if e['current_w'][i]>0 else -1;lo,hi=sorted([sign*v[i]for v in e['nominal_centered_first_alpha_interval']]);a=sign*e['selected_alpha'][i];forced=lo>0;color='#B2473B'if forced else'#2463A6';left.plot([lo,hi],[7-i]*2,lw=5,color=color,solid_capstyle='round');left.plot(a,7-i,'o',ms=6,color=color);left.text(.027,7-i,'forced increase'if forced else'braking direction allowed',va='center',fontsize=9,color=color);writer.writerow(['alpha_interval',i+1,lo,a,hi,'rad/s^2'])
left.axvline(0,color='#555555',ls='--',lw=1);left.set_yticks(range(1,8),[f'Joint {i}'for i in range(7,0,-1)]);left.set_xlim(-.02,.05);left.set_ylim(.5,7.6);left.set_xticks([-.02,-.01,0,.01,.02]);left.set_xlabel('First alpha × sign(current w) (rad/s²)');left.set_title('Current43, accepted trial1: narrow alpha interval',loc='left',fontsize=11,pad=20);left.text(-.019,7.65,'Negative: decreases |w|',fontsize=9,color='#2463A6');left.text(.004,7.65,'Positive: increases |w|',fontsize=9,color='#B2473B')
ratios=[x['at800ms']['v']/1e-4 for x in f];right.bar(range(4),ratios,color='#657F9D',width=.55);right.axhline(1,color='#555555',ls='--',lw=1);right.set_xticks(range(4),[x['case']for x in f]);right.set_xlabel('Saved current / accepted trial');right.set_ylabel('Predicted physical speed / original 1e-4 rad/s limit');right.set_ylim(0,13);right.set_title('Fixed saved forecasts: speed after800ms',loc='left',fontsize=11,pad=20)
for i,x in enumerate(ratios):right.text(i,x+.22,f'{x:.2f}×',ha='center',fontsize=10);writer.writerow(['forecast_speed_ratio',f[i]['case'],'',x,'','threshold ratio'])
fig.suptitle('Attempt61: retained braking restrictions and physical response',x=.06,ha='left',fontsize=15)
fig.text(.06,.09,'All7 joint intervals and all4 selected forecast cases shown. Same recorded61 data; no new simulation or controller call.\nForecast tails describe fixed candidates, not later actual motion. No successful stop, complete task or phase acceptance.',fontsize=9)
fig.subplots_adjust(left=.07,right=.98,top=.77,bottom=.25,wspace=.55)
outputs={'csv':table.getvalue().encode()}
for ext in['png','svg']:
 b=io.BytesIO();fig.savefig(b,format=ext,dpi=180,facecolor='white');outputs[ext]=b.getvalue()
plt.close(fig)
provenance=dict(schema='SAVED61_BRAKING_CAUSE_STATIC_FIGURE_V1',source_pins=pins,interval_case=e['case'],sign_convention='alpha multiplied by sign(current accepted w); positive means instantaneous growth of |w|',selection='All7 joints of actual61 accepted43/1. Four predefined accepted current forecasts32/1,43/1,74/0,95/0; no extrapolation or omitted case in this reviewed set. Not all actual61 forecasts.',scope='Recorded development diagnostics only. New braking repair not verified by this image. No Model/plant/native calls.',renderer=dict(sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),matplotlib=matplotlib.__version__,font='DejaVu Sans',dpi=180),outputs={k:dict(bytes=len(v),sha256=hashlib.sha256(v).hexdigest())for k,v in outputs.items()})
outputs['json']=(json.dumps(provenance,indent=2)+'\n').encode();assert sum(map(len,outputs.values()))<2*1024**2
for ext,b in outputs.items():bounded_write_bytes(O/('saved61_braking_cause.'+ext),b)
print(json.dumps({k:len(v)for k,v in outputs.items()}))
