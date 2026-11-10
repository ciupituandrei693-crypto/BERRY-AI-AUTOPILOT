"""Real local Shorts/preview frame extraction from a video using installed FFmpeg.
Usage: python tools/make_short.py input.mp4 output_short.mp4 --start 0
No cloud, no AI; creates a real 15-second vertical cut or padding.
"""
from __future__ import annotations
import argparse
import shutil
import subprocess
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('input',type=Path);parser.add_argument('output',type=Path)
parser.add_argument('--start',type=float,default=0.0)
args=parser.parse_args()
if shutil.which('ffmpeg') is None:raise SystemExit('FFmpeg nu este instalat sau nu se afla in PATH')
if not args.input.is_file():raise SystemExit('Nu există fișierul video de intrare')
if args.input.resolve()==args.output.resolve():raise SystemExit('Intrarea și ieșirea trebuie să fie diferite')
args.output.parent.mkdir(parents=True,exist_ok=True)
subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',str(max(0,args.start)),
               '-i',str(args.input),'-t','15','-vf','scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1',
               '-c:v','libx264','-preset','veryfast','-crf','22','-c:a','aac','-movflags','+faststart',str(args.output)],check=True)
print('Short gata:',args.output)
