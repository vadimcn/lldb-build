import os
import tempfile
import zipfile
import shutil
import platform
import re
from subprocess import call, check_call, check_output
from pathlib import Path
from os.path import join

from .utils import *


def build_lldb(work_dir: Path, cfg: Dict[str, str], build_type: str, *,
               python_exe: Path,
               python_lib: Path) -> Path:
    
    llvm_src = Path(__file__).resolve().parent.parent / 'llvm-project' / 'llvm'
    llvm_build = work_dir / 'llvm'
    llvm_build.mkdir(exist_ok=True)

    cmake_args = {
        'CMAKE_BUILD_TYPE': build_type,
        'LLVM_ENABLE_PROJECTS': 'clang;lldb',
        'LLVM_ENABLE_RUNTIMES': 'libcxx',
        'LLVM_TARGETS_TO_BUILD': 'AArch64;ARM;AVR;MSP430;RISCV;X86;WebAssembly',
        'LLVM_EXPERIMENTAL_TARGETS_TO_BUILD': 'Xtensa',
        'LLVM_PARALLEL_LINK_JOBS': '1',
        'LLVM_VERSION_SUFFIX': '-codelldb',
        'LLVM_APPEND_VC_REV': 'FALSE',
        'LLVM_ENABLE_ZSTD': 'FALSE',
        'LLVM_ENABLE_LIBXML2': 'FORCE_ON',
        'LLDB_ENABLE_PYTHON': 'TRUE',
        'LLDB_EMBED_PYTHON_HOME': 'TRUE',
        'LLDB_PYTHON_HOME': '..',
        'LLDB_PYTHON_RELATIVE_PATH': 'lib/lldb-python',
        'LLDB_PYTHON_EXE_RELATIVE_PATH': 'python3',
        'LLDB_PYTHON_EXT_SUFFIX': '.so',
        'LLDB_ENABLE_CURSES': 'FALSE',
        'LLDB_ENABLE_LZMA': 'FALSE',
    }

    cmake_args.update(cfg)  # type: ignore

    targets_to_build = ['lldb', 'lldb-server', 'llvm-dwarfdump', 'llvm-pdbutil', 'llvm-readobj']

    if cfg['CMAKE_SYSTEM_PROCESSOR'] != platform.machine():
        cmake_args.update({
            'CMAKE_CROSSCOMPILING': 'ON',
            'CROSS_TOOLCHAIN_FLAGS_NATIVE': '-DLLVM_ENABLE_PROJECTS=clang'
        })

    if cfg['CMAKE_SYSTEM_NAME'] == 'Linux':
        cmake_args.update({
            'CMAKE_EXE_LINKER_FLAGS': cmake_args.get('CMAKE_EXE_LINKER_FLAGS', '') + ' -L' + str(python_lib.parent),
            'CMAKE_SHARED_LINKER_FLAGS': cmake_args.get('CMAKE_SHARED_LINKER_FLAGS', '') + ' -L' + str(python_lib.parent),
            'LLVM_ENABLE_ZLIB': 'FORCE_ON',
            'LLVM_ENABLE_ZSTD': 'FORCE_ON',
            'LLVM_USE_STATIC_ZSTD': 'TRUE',
        })

    if cfg['CMAKE_SYSTEM_NAME'] == 'Darwin':
        cmake_args.update({
            'LLDB_USE_SYSTEM_DEBUGSERVER': 'ON',
            'LLVM_ENABLE_ZLIB': 'FORCE_ON',
        })

    if cfg['CMAKE_SYSTEM_NAME'] == 'Windows':
        cmake_args.update({
            'CMAKE_C_FLAGS': '-DLIBXML_STATIC=1',
            'CMAKE_CXX_FLAGS': '-DLIBXML_STATIC=1',
        })

    cmake_args = dict_to_cmake(cmake_args)
    print('Configuring LLVM with:')
    for a in cmake_args:
        print(' ', a)

    os.environ['PATH'] = str(python_exe.parent) + os.pathsep + os.environ['PATH']

    check_call(['cmake', '-GNinja', str(llvm_src), '-B', str(llvm_build)] + cmake_args)

    for target in targets_to_build:
        print('Building', target)
        check_call(['cmake', '--build', str(llvm_build), '--target', target])

    return llvm_build


def package_lldb(llvm_src: Path, llvm_build: Path, python_dist: Path, cfg: dict[str, str],
                 output_zip: Path, debug_output_zip: Path, release_package: bool = False):

    compression = zipfile.ZIP_DEFLATED if release_package else zipfile.ZIP_STORED
    with tempfile.TemporaryDirectory() as temp_dir, \
            zipfile.ZipFile(output_zip, 'w', compression=compression) as zip, \
            zipfile.ZipFile(debug_output_zip, 'w', compression=compression) as debug_zip:

        if not release_package:
            debug_zip = None

        def exclude_lldb(files: PathDuples):
            for abspath, relpath in files:
                if not os.path.basename(relpath).startswith('_lldb.'):
                    yield abspath, relpath

        tempbin = Path(temp_dir) / 'tempbin'

        def strip_binaries(files: PathDuples) -> PathDuples:
            if release_package:
                for abspath, relpath in files:
                    shutil.copy(abspath, tempbin)
                    check_call([cfg['CMAKE_STRIP'], tempbin])
                    yield tempbin, relpath
            else:
                for abspath, relpath in files:
                    yield abspath, relpath

        # lldb
        lldb_includes = [
            'include/lldb/lldb-*.h',
            'include/lldb/API/*.h',
        ]
        files = rel_glob(llvm_src / 'lldb', lldb_includes)
        add_to_zip(files, zip)

        files = rel_glob(llvm_build / 'tools/lldb', 'include/lldb/API/*.h')
        add_to_zip(files, zip)

        target_os = cfg['CMAKE_SYSTEM_NAME']
        if target_os == 'Linux':

            lldb_files = [
                'bin/lldb',
                'bin/lldb-argdumper',
                'bin/lldb-server',
                'lib/liblldb.*'
            ]
            files = rel_glob(llvm_build, lldb_files)
            add_to_zip(strip_binaries(files), zip)

            lldb_debug_files = [
                'bin/lldb',
                'bin/lldb-argdumper',
                'bin/lldb-server',
                'bin/llvm-dwarfdump',
                'bin/llvm-pdbutil',
                'bin/llvm-readobj',
                'lib/liblldb.*'
            ]
            files = rel_glob(llvm_build, lldb_files)
            add_to_zip(files, debug_zip)

            python_files = rel_glob(llvm_build, 'lib/lldb-python/**/*')
            compose(python_files, exclude_lldb, (add_to_zip, zip))

        elif target_os == 'Darwin':

            # Fix install_name of Python in liblldb.dylib
            shutil.copy(join(llvm_build, 'lib/liblldb.dylib'), tempbin)
            output = check_output(['otool', '-L', str(tempbin)], encoding='utf8')
            regex = re.compile(r'^\s*(.*(libpython3.*))\s\(', re.MULTILINE)
            match = regex.search(output)
            assert match is not None
            oldname = match.group(1)
            newname = '@rpath/' + match.group(2)
            check_call(['install_name_tool', '-change', oldname, newname, tempbin])
            add_to_zip([(tempbin, Path('lib/liblldb.dylib'))], zip)

            lldb_files = [
                'bin/lldb',
                'bin/lldb-argdumper',
                'bin/lldb-server',
                'bin/debugserver',
            ]
            files = rel_glob(llvm_build, lldb_files)
            add_to_zip(files, zip)
            for abspath, _ in files:
                dsymname = os.path.splitext(abspath)[0] + '.dSYM'
                call(['dsymutil', abspath, '-o', dsymname])

            lldb_debug_files = [
                'bin/llvm-dwarfdump',
                'bin/llvm-pdbutil',
                'bin/llvm-readobj',
                'bin/lldb.dSYM/**/*',
                'bin/lldb-argdumper.dSYM/**/*',
                'bin/lldb-server.dSYM/**/*',
                'bin/llvm-dwarfdump.dSYM/**/*',
                'bin/llvm-pdbutil.dSYM/**/*',
                'bin/llvm-readobj.dSYM/**/*',
                'lib/liblldb*.dSYM/**/*',
            ]
            add_to_zip(rel_glob(llvm_build, lldb_debug_files), debug_zip)

            python_files = rel_glob(llvm_build, 'lib/lldb-python/**/*')
            compose(python_files, exclude_lldb, (add_to_zip, zip))

        elif target_os == 'Windows':

            lldb_files = [
                'bin/lldb.exe',
                'bin/lldb-argdumper.exe',
                'bin/lldb-server.exe',
                'bin/liblldb.dll',
                'lib/liblldb.lib',
            ]
            add_to_zip(rel_glob(llvm_build, lldb_files), zip)

            redist = Path(os.environ['VCToolsRedistDir'])
            vcrt_files = [
                'x64/Microsoft.VC*.CRT/vcruntime140*.dll',
                'x64/Microsoft.VC*.CRT/msvcp140.dll',
            ]

            def set_prefix(files: PathDuples):
                for abspath, _ in files:
                    yield abspath, Path('bin') / abspath.name

            compose(rel_glob(redist, vcrt_files), set_prefix, (add_to_zip, zip))

            lldb_debug_files = [
                'bin/lldb.pdb',
                'bin/lldb-argdumper.pdb',
                'bin/lldb-server.pdb',
                'bin/llvm-dwarfdump.exe',
                'bin/llvm-dwarfdump.pdb',
                'bin/llvm-pdbutil.exe',
                'bin/llvm-pdbutil.pdb',
                'bin/llvm-readobj.exe',
                'bin/llvm-readobj.pdb',
                'bin/liblldb.pdb',
            ]
            add_to_zip(rel_glob(llvm_build, lldb_debug_files), debug_zip)

            python_files = rel_glob(llvm_build, 'lib/lldb-python/**/*')
            compose(python_files, exclude_lldb, (add_to_zip, zip))

        else:
            raise Exception('Unknown target')

        # Python distro
        compose(rel_glob(python_dist, '**/*'), (add_to_zip, zip))
