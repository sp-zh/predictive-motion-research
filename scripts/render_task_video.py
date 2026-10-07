#!/usr/bin/env python3
"""Render saved executed states; never rerun control or integrate new motion.

Requires MuJoCo 3.3.7, NumPy, Pillow and ffmpeg, plus the pinned FR3 assets
and the generated inspection scene. Raw CSVs remain in the evidence archive.
"""
import argparse
import csv
import hashlib
import json
import subprocess
from pathlib import Path

import mujoco
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--csv', type=Path, required=True)
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--scene', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--title', required=True)
    parser.add_argument('--azimuth', type=float, default=135)
    parser.add_argument('--distance', type=float, default=1.5)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.output.exists():
        raise ValueError('Refusing to overwrite an existing published video')
    # Check the complete pinned upstream asset set before rendering.
    asset_root = root / '.vendor/menagerie'
    asset_manifest = root / 'src/predictive_motion_description/manifests/fr3.sha256'
    for line in asset_manifest.read_text().splitlines():
        expected, name = line.split(None, 1)
        if sha(asset_root / name.strip()) != expected:
            raise ValueError('Pinned asset hash mismatch: ' + name)
    summary = {}
    for line in args.summary.read_text().splitlines():
        key, value = line.split(':', 1)
        summary[key] = value.strip().strip('"')
    if summary['completed'] != 'true':
        raise ValueError('Showcase video requires a completed run')
    with args.csv.open() as stream:
        rows = list(csv.DictReader(stream))
    times = np.array([float(row['time_s']) for row in rows])
    if not np.all(np.diff(times) > 0):
        raise ValueError('Nonmonotonic replay time')
    q = np.array([[float(row[f'q_post_{i}']) for i in range(1, 8)] for row in rows])
    if not np.all(np.isfinite(q)) or len(rows) != int(summary['rows']):
        raise ValueError('Invalid replay states or row count')
    for name in ['cad/source/inspection.json', 'cad/source/simulation.json',
                 'cad/generated/tool_visual.stl', 'cad/generated/fixture_visual.stl',
                 'benchmarks/reference/inspection_curve.json']:
        frozen = root / 'results/phase4-export/predictive_motion' / name
        if not frozen.is_file() or sha(frozen) != sha(root / name):
            raise ValueError('Render geometry/reference differs from frozen input: ' + name)
    model = mujoco.MjModel.from_xml_path(str(args.scene.resolve()))
    width, height, fps = 1280, 720, 30
    model.vis.global_.offwidth = width
    model.vis.global_.offheight = height
    data = mujoco.MjData(model)
    addresses = [model.jnt_qposadr[mujoco.mj_name2id(
        model, mujoco.mjtObj.mjOBJ_JOINT, f'fr3_joint{i}')] for i in range(1, 8)]
    camera = mujoco.MjvCamera()
    mujoco.mjv_defaultCamera(camera)
    camera.lookat[:] = [.49, -.01, .49]
    camera.distance = args.distance
    camera.azimuth = args.azimuth
    camera.elevation = -23
    renderer = mujoco.Renderer(model, height=height, width=width)
    reference = json.loads((root / 'benchmarks/reference/inspection_curve.json').read_text())
    start, end = np.array(reference['start']), np.array(reference['end'])
    s = np.linspace(0, 1, 81)
    path = start[None, :] + s[:, None] * (end - start)[None, :]
    path[:, 1] += reference['lateral_amplitude'] * np.sin(2 * np.pi * s)
    path[:, 2] += reference['vertical_amplitude'] * np.sin(np.pi * s)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    partial = args.output.with_suffix('.part.mp4')
    font_path = Path('/System/Library/Fonts/Supplemental/Arial.ttf')
    font = ImageFont.truetype(str(font_path), 25) if font_path.exists() else ImageFont.load_default(size=25)
    small = ImageFont.truetype(str(font_path), 20) if font_path.exists() else ImageFont.load_default(size=20)
    command = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo',
               '-pixel_format', 'rgb24', '-video_size', f'{width}x{height}',
               '-framerate', str(fps), '-i', '-', '-an', '-c:v', 'libx264',
               '-preset', 'fast', '-crf', '21', '-pix_fmt', 'yuv420p',
               '-movflags', '+faststart', str(partial)]
    encoder = subprocess.Popen(command, stdin=subprocess.PIPE)
    frame_times = np.arange(int(round(times[-1] * fps))) / fps
    selected = []
    try:
        for frame, t in enumerate(frame_times):
            # Nearest actual post-step record. No interpolated or synthetic poses.
            right = int(np.clip(np.searchsorted(times, t), 0, len(times) - 1))
            left = max(0, right - 1)
            index = left if abs(times[left] - t) < abs(times[right] - t) else right
            selected.append(index)
            data.qpos[addresses] = q[index]
            data.time = times[index]
            mujoco.mj_forward(model, data)
            renderer.update_scene(data, camera=camera)
            # Reference trace is a visual overlay, not part of collision geometry.
            for a, b in zip(path[:-1], path[1:]):
                geom = renderer.scene.geoms[renderer.scene.ngeom]
                mujoco.mjv_initGeom(geom, mujoco.mjtGeom.mjGEOM_CAPSULE,
                                   np.zeros(3), np.zeros(3), np.eye(3).reshape(-1),
                                   np.array([.20, .95, .83, 1.]))
                mujoco.mjv_connector(geom, mujoco.mjtGeom.mjGEOM_CAPSULE, .0015, a, b)
                renderer.scene.ngeom += 1
            image = Image.fromarray(renderer.render())
            draw = ImageDraw.Draw(image)
            draw.rectangle((0, 0, width, 90), fill='#101d30')
            draw.text((24, 14), args.title, font=font, fill='white')
            draw.text((24, 50), 'FR3 inspection | Phase 4 | recorded-state simulation replay | 1x speed',
                      font=small, fill='#b8cedf')
            row = rows[index]
            label = (f"t = {times[index]:05.2f} s   |   position error {float(row['pose_position_m'])*1000:.3f} mm"
                     f"   |   model clearance {float(row['true_clearance_m'])*1000:.2f} mm")
            draw.rectangle((0, height - 45, width, height), fill='#101d30')
            draw.text((24, height - 33), label, font=small, fill='white')
            encoder.stdin.write(image.tobytes())
            if frame in [0, len(frame_times)//2, len(frame_times)-1]:
                suffix = ['start', 'middle', 'end'][[0, len(frame_times)//2, len(frame_times)-1].index(frame)]
                image.save(args.output.with_name(args.output.stem + '-' + suffix + '.jpg'))
        encoder.stdin.close()
        if encoder.wait() != 0:
            raise RuntimeError('Video encoding failed')
    finally:
        renderer.close()
        if encoder.poll() is None:
            encoder.kill()
    partial.rename(args.output)
    metadata = {
        'scope': 'Curated successful Phase 4 diagnostic replay; not a new trial or Phase 5 result',
        'selection': 'Three methods; completed evaluation seed 81011 selected for lower peak position error than seed 81012. QP seed 81012 failed and remains retained.',
        'method': summary['method'], 'seed': int(summary['seed']), 'summary': summary,
        'source_csv': str(args.csv.resolve().relative_to(root)), 'source_csv_sha256': sha(args.csv),
        'source_summary_sha256': sha(args.summary),
        'original_evidence_archive_sha256': '1e3ec6da7a8fb60a090aafa5d78405643624be6e4067c029af197d8dd5f17303',
        'upstream_commit': json.loads((root / 'src/predictive_motion_description/manifests/fr3.json').read_text())['commit'],
        'upstream_asset_manifest_sha256': sha(asset_manifest),
        'render_script_sha256': sha(Path(__file__)),
        'scene_manifest': json.loads((args.scene.parent / 'scene_manifest.json').read_text()),
        'mujoco_version': mujoco.__version__, 'fps': fps, 'frames': len(frame_times),
        'duration_s': len(frame_times)/fps, 'speed': 1,
        'render_state': 'nearest saved q_post at each frame, mj_forward only; no control or physics stepping',
        'max_sampling_time_error_s': float(np.max(np.abs(times[selected] - frame_times))),
        'camera': {'azimuth': args.azimuth, 'distance': args.distance, 'elevation': -23},
        'video_sha256': sha(args.output), 'video_bytes': args.output.stat().st_size,
    }
    args.output.with_suffix('.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print(json.dumps({'video': str(args.output), 'frames': len(frame_times), 'bytes': metadata['video_bytes']}))


if __name__ == '__main__':
    main()
