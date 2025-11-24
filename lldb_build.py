#!/usr/bin/env python3
import argparse
import os
import platform
import subprocess
import sys
from glob import glob
from pathlib import Path
from subprocess import check_call

parser = argparse.ArgumentParser()
parser.add_argument('--build-dir', type=Path, default='.')
parser.add_argument('--python-standalone', type=Path, default='.')
args, unknown = parser.parse_known_args()

source_dir = Path(__file__).resolve().parent

args.build_dir.mkdir(exist_ok=True)
python_dir = args.build_dir / 'python'

if platform.system() == 'Windows':
    arch = 'x86_64'
    system = 'windows'
    python3 = python_dir / 'install' / 'python.exe'
else:
    system = platform.system().lower()
    arch = platform.machine()
    if system == 'darwin' and arch == 'arm64':
        arch = 'aarch64'
    python3 = python_dir / 'install' / 'bin' / 'python3'

print('Host is', system, arch)

if not python_dir.exists():
    python_dir.mkdir(exist_ok=True)
    pattern = str(args.python_standalone / ('cpython-*-' + arch + '*-*-' + system + '-*.tar.zst'))
    cpython_archive = glob(pattern)[0]
    zstd = subprocess.Popen(['zstd', '-dcf', cpython_archive], stdout=subprocess.PIPE)
    check_call(['tar', '--strip-components=1', '-xf', '-'], stdin=zstd.stdout, cwd=str(python_dir))

os.environ['PYTHONPATH'] = str(source_dir)
check_call([str(python3), '-u', '-m', 'lldb_build'] + sys.argv[1:], cwd=str(args.build_dir))
