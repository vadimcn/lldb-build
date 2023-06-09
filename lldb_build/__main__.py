import sys
import argparse
from pathlib import Path
from glob import glob
import subprocess
from subprocess import check_call
from typing import Any

from .libxml2 import build_libxml2
from .python import build_lldb_python
from .lldb import build_lldb, package_lldb
from .target import get_target_config


def main(args: Any):
    work_dir = args.build_dir.resolve()
    cfg = get_target_config(args.target)
    if args.sysroot:
        cfg['CMAKE_SYSROOT'] = str(args.sysroot)

    target_python_archive = cfg.get('TARGET_PYTHON_ARCHIVE')
    if target_python_archive is None:
        python_dist = work_dir / 'python'
    else:
        python_dist = work_dir / 'python_dist'
        if not python_dist.exists():
            cpython_archive = glob(str(args.python_standalone / target_python_archive))[0]
            python_dist.mkdir(exist_ok=True)
            zstd = subprocess.Popen(['zstd', '-dcf', cpython_archive], stdout=subprocess.PIPE)
            check_call(['tar', '--strip-components=1', '-xf', '-'], stdin=zstd.stdout, cwd=str(python_dist))

    print('Using python_dist:', python_dist)
    python_lldb = work_dir / 'python_lldb'
    python_exe = Path(sys.executable)
    python_inc, python_lib = build_lldb_python(python_dist, python_lldb, cfg)

    libxml_inc, libxml_lib = build_libxml2(work_dir, cfg, args.build_type)

    llvm_build = build_lldb(work_dir, cfg, args.build_type,
                            ccache=args.ccache,
                            libxml_inc=libxml_inc, libxml_lib=libxml_lib,
                            python_exe=python_exe, python_inc=python_inc, python_lib=python_lib)

    lldb_archive = work_dir / f'lldb--{args.target}.zip'
    lldb_debug_archive = work_dir / f'lldb-debug--{args.target}.zip'

    llvm_src = Path(__file__).resolve().parent.parent / 'llvm-project'
    package_lldb(llvm_src, llvm_build, python_lldb, cfg, lldb_archive, lldb_debug_archive,
                 release_package=args.release_package)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', required=True)
    parser.add_argument('--python-standalone', type=Path, required=True)
    parser.add_argument('--build-dir', type=Path, default='.')
    parser.add_argument('--build-type', default='MinSizeRel')
    parser.add_argument('--release-package', action='store_true')
    parser.add_argument('--sysroot', type=Path)
    parser.add_argument('--ccache', type=Path)
    args = parser.parse_args()
    main(args)
