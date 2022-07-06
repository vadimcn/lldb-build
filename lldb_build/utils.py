import os
import shutil
import math
from os.path import join
from fnmatch import fnmatch
from glob import glob
from pathlib import Path
from zipfile import ZipFile
from typing import Iterable, List, Optional, Tuple, Union,  Any, Dict


def out_of_date(outputs: Iterable[Path], inputs: Iterable[Path]):
    '''Checks whether any outputs are out-of-date with respect to inputs.  Inputs may contain globs.'''
    min_output_time = math.inf
    for file in outputs:
        if not os.path.exists(file):
            return True
        stat = os.stat(file)
        min_output_time = min(min_output_time, stat.st_mtime_ns)

    max_input_time = 0
    for pattern in inputs:
        for file in glob(str(pattern), recursive=True):
            stat = os.stat(file)
            max_input_time = max(max_input_time, stat.st_mtime_ns)

    return max_input_time > min_output_time


def compose(it: Iterable[Any], *transforms: Any) -> Iterable[Any]:  # TODO: precise type
    '''Apply transforms to an iterator.  A transform must be either a callable or a tuple (callable, arg1, arg2, ...)'''
    for transform in transforms:
        if type(transform) is tuple:
            fn, *args = transform
            it = fn(it, *args)
        else:
            it = transform(it)
    return it


PathDuples = Iterable[Tuple[Path, Path]]


def rel_glob(basedir: Path, patterns: Union[str, List[str]]) -> PathDuples:
    if type(patterns) is str:
        patterns = [patterns]
    return iter([(Path(abspath), Path(os.path.relpath(abspath, basedir)))
                 for pattern in patterns
                 for abspath in glob(join(basedir, pattern), recursive=True)])


def exclude(files: PathDuples, excludes: List[str]) -> PathDuples:
    for abspath, relpath in files:
        if not any([fnmatch(str(relpath), exclude) for exclude in excludes]):
            yield abspath, relpath


def rel_prefix(files: PathDuples, prefix: Path) -> PathDuples:
    for abspath, relpath in files:
        yield abspath, prefix / relpath


def add_to_zip(files: PathDuples, zipfile: Optional[ZipFile]):
    if zipfile is None:
        return
    for abspath, relpath in files:
        #print('Adding ', relpath)
        zipfile.write(abspath, relpath)


def copy_to(files: PathDuples, target: Path):
    for abspath, relpath in files:
        file_target = target / relpath
        os.makedirs(os.path.dirname(file_target), exist_ok=True)
        shutil.copy(abspath, target / relpath)


def inspect(files: PathDuples) -> PathDuples:
    for abspath, relpath in files:
        print('###', abspath, relpath)
        yield abspath, relpath


def dict_to_cmake(cmake_args: Dict[str, str]):
    return [f'-D{key}={val}' for key, val in cmake_args.items()]
