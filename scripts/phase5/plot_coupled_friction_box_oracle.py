#!/usr/bin/env python3
"""Render an existing public nominal box-QP counterexample; no new solves."""
import argparse
import hashlib
import json
from pathlib import Path
SOURCE=Path(__file__).resolve()
SOURCE_BYTES=SOURCE.read_bytes()
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

def sha(data):return hashlib.sha256(data).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();data_bytes=args.input.read_bytes();data=json.loads(data_bytes)
    fixture=next(f for f in data['fixtures'] if f['name']=='axis_clip_counterexample')
    optimal=np.array(fixture['force']);clipped=np.array(fixture['naive_axis_clip']['force']);bounds=np.array(data['friction_bounds'])
    index=np.arange(7);fig,ax=plt.subplots(figsize=(11.5,6.4));fig.patch.set_facecolor('#f8fafc');ax.set_facecolor('#ffffff')
    width=.32
    ax.bar(index-width/2,clipped,width,label='Coordinatewise clip',color='#6c8196',zorder=3)
    ax.bar(index+width/2,optimal,width,label='Coupled QP optimum',color='#c75422',zorder=3)
    for i,limit in enumerate(bounds):
        ax.hlines([limit,-limit],i-.4,i+.4,colors='#292e36',linewidth=1.15,zorder=4)
    ax.plot([],[],color='#292e36',lw=1.15,label='Frozen friction-box limits')
    ax.axhline(0,color='#6b7280',lw=.8);ax.set_xticks(index,[str(i+1) for i in index]);ax.set_xlabel('Joint',fontsize=12)
    ax.set_ylabel('Friction force (N m)',fontsize=12);ax.set_ylim(-1.34,1.48);ax.set_yticks(np.arange(-1.2,1.3,.4))
    ax.grid(axis='y',color='#e5e7eb',linewidth=.8,zorder=0);ax.spines[['top','right']].set_visible(False)
    ax.legend(loc='upper right',frameon=False,fontsize=10,ncol=1)
    ax.annotate('Clipping leaves a large\nfree-joint KKT residual',xy=(2-width/2,clipped[2]),xytext=(.55,-.78),fontsize=11,color='#364152',arrowprops={'arrowstyle':'->','color':'#6c8196','lw':1.3},ha='center')
    fig.text(.08,.946,'Coupled friction box QP: clipping is not the optimum',fontsize=18,weight='bold',color='#162231')
    fig.text(.08,.901,'Synthetic drive  |  public nominal seven-joint model  |  model algebra, not a physical trial',fontsize=11,color='#526070')
    residual=fixture['naive_axis_clip']['original_KKT']['KKT_residual'];optres=fixture['original_KKT']['KKT_residual']
    fig.text(.08,.109,f'Original KKT residual: clip {residual:.5f} vs coupled {optres:.2e} rad/s²',fontsize=12,color='#162231')
    fig.text(.08,.065,f'Max force difference {fixture["naive_axis_clip"]["max_force_error"]:.5f} N m   |   QP objective gap {fixture["naive_axis_clip"]["objective_loss"]:.5f} (algebra)',fontsize=11,color='#526070')
    fig.subplots_adjust(left=.08,right=.975,bottom=.22,top=.845)
    args.output.mkdir(parents=True,exist_ok=False);png=args.output/'phase5_coupled_friction_box_oracle.png';fig.savefig(png,dpi=180,facecolor=fig.get_facecolor());plt.close(fig)
    assert SOURCE.read_bytes()==SOURCE_BYTES and args.input.read_bytes()==data_bytes
    meta={'scope':'Existing synthetic drive/public nominal model algebra; not physical trial, model prediction validation or Phase5 acceptance','source_sha256':sha(SOURCE_BYTES),'oracle_json_sha256':sha(data_bytes),'oracle_source_sha256':data['source_sha256'],'public_model_review_sha256':data['public_input_sha256'],'fixture_name':fixture['name'],'matrix_origin':'inspection MJCF imported into Pinocchio 4.1; public nominal M with armature/tool payload plus compiled MuJoCo 3.3.7 invweight0 regularizer','M':data['M'],'R':data['R'],'H':data['H'],'ell':fixture['ell'],'synthetic_velocity':fixture['synthetic_velocity'],'frozen_bounds_Nm':bounds.tolist(),'optimal_force_Nm':optimal.tolist(),'axis_clip_force_Nm':clipped.tolist(),'coupled_KKT':fixture['original_KKT'],'clip_KKT':fixture['naive_axis_clip']['original_KKT'],'objective_gap':fixture['naive_axis_clip']['objective_loss'],'max_force_difference_Nm':fixture['naive_axis_clip']['max_force_error'],'png_sha256':sha(png.read_bytes()),'matplotlib_version':matplotlib.__version__,'data_unchanged':True,'new_solves':0}
    (args.output/'phase5_coupled_friction_box_oracle.json').write_text(json.dumps(meta,indent=2)+'\n');(args.output/'SOURCE_SNAPSHOT.py').write_bytes(SOURCE_BYTES);(args.output/'ORACLE_INPUT_SNAPSHOT.json').write_bytes(data_bytes)
    files={f.name:{'sha256':sha(f.read_bytes()),'bytes':f.stat().st_size} for f in args.output.iterdir()}
    assert SOURCE.read_bytes()==SOURCE_BYTES and args.input.read_bytes()==data_bytes
    (args.output/'READY.json').write_text(json.dumps({'source_sha256':sha(SOURCE_BYTES),'files':files},indent=2)+'\n')
    print(json.dumps({'png_sha256':meta['png_sha256'],'source_sha256':meta['source_sha256'],'files':files}))

if __name__=='__main__':main()
