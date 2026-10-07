#!/usr/bin/env python3
"""Annotate a new recorded-state MuJoCo render, not a new control/physics trajectory."""
import argparse,csv,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from servo_model_v1 import sha,write_new
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',type=Path,required=True);a=p.parse_args()
root=a.project;case=root/'results/phase5/development/servo-expanded-failure-stop-replay-v1';base=case/'figures';ppm=base/'recorded_failure_state.ppm'
raw=Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw/servo-soft-friction-v2-expanded-validation/raw.csv');row=list(csv.DictReader(raw.open()))[-1]
original=Image.open(ppm);image=Image.new('RGB',(1280,840),'#101d30');image.paste(original,(0,88));draw=ImageDraw.Draw(image)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',28);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',19)
draw.text((26,17),'FR3 recorded failure state | guarded stop rejected',font=font,fill='white')
draw.text((26,55),'MuJoCo 3.3.7 · saved measured q/v and accepted target · forward geometry only',font=small,fill='#b8cedf')
draw.rectangle((0,750,1280,840),fill='#101d30')
draw.text((26,766),f'Virtual t={float(row["time_s"]):.3f} s · recorded clearance={float(row["true_clearance_m"])*1000:.2f} mm · contacts={row["contacts"]}',font=small,fill='white')
draw.text((26,800),'No new command or physics integration in this render. No completed bounded stop or expanded model acceptance.',font=small,fill='#b8cedf')
out=base/'phase5_servo_guard_failure_state.png';image.save(out)
inputs=[raw,ppm,root/'experiments/generated/inspection/scene.xml',root/'experiments/generated/inspection/inspection_fr3.xml',root/'tools/phase5_servo_diagnostics/render_servo_recorded_pose.cpp',root/'build-servo-qp-reconstruct-v1/render_servo_recorded_pose',Path(__file__)]
asset_manifest=root/'src/predictive_motion_description/manifests/fr3.sha256'
for line in asset_manifest.read_text().splitlines():
 expected,name=line.split(None,1)
 if sha(root/'.vendor/menagerie'/name.strip())!=expected:raise ValueError('upstream asset identity')
meta={'scope':__doc__,'source_hashes':{str(f):sha(f) for f in inputs},'upstream_asset_manifest_sha256':sha(asset_manifest),
      'camera':{'lookat_m':[.49,-.01,.49],'distance_m':1.5,'azimuth_deg':135,'elevation_deg':-23},
      'model_length_units':'metres; joint q in radians; no CAD geometry or model units modified',
      'record':{'tick':int(row['tick']),'substep':int(row['substep']),'virtual_time_s':float(row['time_s']),'q_post_rad':[float(row['q_post_'+str(j)]) for j in range(7)]},
      'mujoco_version':'3.3.7','renderer':'existing OSMesa software OpenGL; mj_forward geometry only; no mj_step','output_sha256':sha(out),'completed_stop':False}
write_new(base/'phase5_servo_guard_failure_state.json',meta);print(sha(out))
