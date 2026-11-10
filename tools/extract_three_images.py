"""Create 3 promotional stills from an approved episode via FFmpeg locally.
Usage: python tools/extract_three_images.py episode.mp4 output_dir
"""
from __future__ import annotations
import argparse
import subprocess
import shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('video',type=Path);p.add_argument('folder',type=Path);p.add_argument('--at',nargs=3,type=int,default=[5,30,60]);a=p.parse_args()
if not shutil.which('ffmpeg'):raise SystemExit('FFmpeg este necesar')
if not a.video.is_file():raise SystemExit('Fișierul video nu există')
a.folder.mkdir(parents=True,exist_ok=True)
for i,s in enumerate(a.at,1):
    dest=a.folder/f'promo_{i}.jpg'
    subprocess.run(['ffmpeg','-y','-hide_banner','-loglevel','error','-ss',str(max(0,s)),'-i',str(a.video),'-frames:v','1','-q:v','2',str(dest)],check=True)
    print(dest)
