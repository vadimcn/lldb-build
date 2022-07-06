#!/usr/bin/env python3
import sys
import os
import argparse
import subprocess
import platform
from subprocess import check_call
from pathlib import Path
from glob import glob

parser = argparse.ArgumentParser()
parser.add_argument('--build-dir', type=Path, default='.')
args, unknown = parser.parse_known_args()

source_dir = Path(__file__).resolve().parent

args.build_dir.mkdir(exist_ok=True)
python = args.build_dir / 'python'

if platform.system() == 'Windows':
    arch = 'x86_64'
    system = 'windows'
    python3 = python / 'install' / 'python.exe'
else:
    arch = platform.machine()
    system = platform.system().lower()
    python3 = python / 'install' / 'bin' / 'python3'

python_standalone = source_dir / 'arch' / system / 'python'

if not python.exists():
    python.mkdir(exist_ok=True)
    pattern = str(python_standalone / ('cpython-*-' + arch + '-*-' + system + '-*.tar.zst'))
    cpython_archive = glob(pattern)[0]
    zstd = subprocess.Popen(['zstd', '-dcf', cpython_archive], stdout=subprocess.PIPE)
    check_call(['tar', '--strip-components=1', '-xf', '-'], stdin=zstd.stdout, cwd=str(python))

os.environ['PYTHONPATH'] = str(source_dir)
check_call([str(python3), '-m', 'lldb_build', '--python-standalone', str(python_standalone)] + sys.argv[1:], cwd=str(args.build_dir))
