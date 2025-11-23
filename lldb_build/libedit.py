from pathlib import Path
from subprocess import check_call
from typing import Dict

from .utils import out_of_date


def build_libedit(work_dir: Path, cfg: Dict[str, str], build_type: str):
    libedit_src = Path(__file__).resolve().parent.parent / 'libedit'
    libedit_buld = work_dir / 'libedit'
    libedit_buld.mkdir(exist_ok=True)
    libedit_install = work_dir / 'libedit' / 'install'
    libedit_lib = libedit_install / 'lib' / 'libedit.a'

    if out_of_date([libedit_lib], [libedit_src / '*.c', libedit_src / '*.h']):
        check_call([str(libedit_src / 'configure'), '--prefix=' + str(libedit_install)], cwd=libedit_buld)
        check_call(['make'], cwd=libedit_buld)
        check_call(['make', 'install'], cwd=libedit_buld)

    return (libedit_install / 'include/editline'), libedit_lib
