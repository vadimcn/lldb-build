#!/usr/bin/env python3
import argparse
from pathlib import Path
from subprocess import check_call

parser = argparse.ArgumentParser()
parser.add_argument('--arch', default='x86_64')
parser.add_argument('--image', default='vadimcn/linux-builder:latest')
args = parser.parse_args()

if args.arch == 'x86_64':
    target = 'x86_64-linux-gnu'
elif args.arch == 'armhf':
    target = 'arm-linux-gnueabihf'
elif args.arch == 'aarch64':
    target = 'aarch64-linux-gnu'
else:
    raise Exception('Unknown arch')

project_root = Path(__file__).resolve().parent
build_dir = project_root / ('build-' + args.arch)

check_call(['docker', 'run', '-it',  '--privileged',
            '-v' f'{project_root}:/workspace/source:ro',
            '-v' f'{project_root}/../llvm-project:/workspace/llvm-project:ro',
            '-v' f'{build_dir}:/workspace/build:rw',
            '-e' 'BUILD_TARGET=' + target,
            '-e' 'BUILD_SOURCESDIRECTORY=/workspace/source',
            '-e' 'AGENT_BUILDDIRECTORY=/workspace/build',
            '-e' 'CMAKE_BUILD_TYPE=RelWithDebInfo',
            '-e' 'SCCACHE_DIR=/workspace/build/.sccache',
            '-e' 'SCCACHE_IDLE_TIMEOUT=60',
            '-w' '/workspace/build',
            '-u' '1000:1000',
            '--memory=16G',
            '--cpus=10',
            '--name=linux-builder-' + args.arch,
            '--rm',
            args.image,
            'bash', '-c', 'export PATH=/workspace/source/arch/linux/bin/:$PATH; bash'])
