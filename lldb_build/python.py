import json
from subprocess import check_call
from itertools import chain
from pathlib import Path
from typing import Dict, Any
from .utils import *


def build_lldb_python(python_dist: Path, output: Path, cfg: Dict[str, str]):
    '''Package python files needed by LLDB.'''

    manifest = json.load(open(python_dist / 'PYTHON.json'))
    major, minor, _ = manifest['python_version'].split('.')

    extensions = manifest['build_info']['extensions']

    extensions['_sha2'][0]['links'] = []  # https://github.com/indygreg/python-build-standalone/pull/312

    # Filter built-in binary modules:
    # The goal is to slim down the Python library, keeping modules that are needed or likely to be needed
    # in the debugger environment (ctypes, json, pip), while excluding bloated ones that are unlikely
    # to be needed (sqlite, curses, tkinter).
    required_mods = ['_ctypes', '_json',  # codelldb
                     '_socket', '_ssl', '_scproxy', '_overlapped', 'select', 'zlib', '_sha1', '_sha2', '_sha3',  # pip
                     '_bz2', '_lzma',  # pandas
                     ]
    allowed_libs = ['m', 'dl', 'expat']

    def should_include(name: str, ext: Dict[str, Any]):
        if ext['required'] or name in required_mods:
            return True
        for lib in ext.get('links', []):
            if lib['name'] not in allowed_libs:
                return False
        return True
    included_ext = {name: variants[0] for name, variants in extensions.items() if should_include(name, variants[0])}
    print('Included extensions:', list(included_ext.keys()))

    target_os = cfg['CMAKE_SYSTEM_NAME']

    stdlib_src = manifest['python_paths']['stdlib']
    if stdlib_src.startswith('..'):  # Bug in python-standalone for cross-builds
        pos = stdlib_src.index('install')
        stdlib_src = stdlib_src[pos:]
    stdlib_src = python_dist / stdlib_src
    stdlib_dist = output / 'lib' if target_os == 'Windows' else output / 'lib' / f'python{major}.{minor}'

    stdlib_files = rel_glob(stdlib_src, ['**/*.py', '**/*.pth', '**/*.pem', '**/*.exe'])
    stdlib_exclude = ['config-*', 'idlelib/*', 'lib2to3/*', 'test/*', 'venv/*',
                      'turtledemo/*', 'tkinter/*', 'curses/*', 'sqlite3/*']
    compose(stdlib_files, (exclude, stdlib_exclude), (copy_to, stdlib_dist))

    if target_os in ['Linux', 'Darwin']:
        c_compiler = [cfg['CMAKE_C_COMPILER']] + cfg['CMAKE_C_FLAGS'].split(' ')
        if 'CMAKE_SYSROOT' in cfg:
            c_compiler += ['--sysroot', cfg['CMAKE_SYSROOT']]
        if 'LLVM_HOST_TRIPLE' in cfg:
            c_compiler += ['-target', cfg['LLVM_HOST_TRIPLE']]
        osx_arch = cfg.get('CMAKE_OSX_ARCHITECTURES')
        if osx_arch is not None:
            c_compiler += ['-arch', osx_arch]

        # Create config.o with _PyImport_Inittab
        with open(python_dist / 'config.c', 'w') as config:
            config.write('#include "Python.h"\n')

            for name, ext in included_ext.items():
                init_fn = ext['init_fn']
                if init_fn != 'NULL':
                    config.write('extern PyObject* {}(void);\n'.format(init_fn))

            config.write('struct _inittab _PyImport_Inittab[] = {\n')
            for name, ext in included_ext.items():
                init_fn = ext.get('init_fn')
                config.write('    {{ "{}", {} }},\n'.format(name, init_fn))
            config.write('    { 0, 0 }\n')
            config.write('};\n')

        check_call(c_compiler + ['-I', str(python_dist / 'install' / 'include' / f'python{major}.{minor}'),
                                 '-c', 'config.c'], cwd=python_dist)

        # Create libpythonXY.so
        objects = chain.from_iterable([manifest['build_info']['core']['objs']] +
                                      [ext['objs'] for ext in included_ext.values()])
        inittab_object = manifest['build_info']['inittab_object']
        objects = ['config.o'] + [str(python_dist / obj) for obj in objects if obj != inittab_object]
        objects = list(set(objects))  # Deduplicate
        check_call(['ar', '-r', 'libpython.a'] + objects, cwd=python_dist)

        libs = ['libpython.a']
        for lib in (lib for ext in included_ext.values() for lib in ext['links']):
            if lib.get('system'):
                libs.append('-l' + lib['name'])
            elif lib.get('framework'):
                libs.append('-Wl,-framework,' + lib['name'])
            else:
                libs.append(python_dist / lib['path_static'])

        (output / 'lib').mkdir(exist_ok=True)

        if target_os == 'Linux':
            with open(python_dist / 'python.exports', 'w') as exports:
                exports.write(f'libpython{major}{minor}.so\n{{\nglobal:\nPy*;_Py*;__Py*;\nlocal:\n*;\n}};\n')

            libs += ['-lpthread', '-lm', '-lutil']
            python_dylib = output / 'lib' / f'libpython{major}{minor}.so'
            cmd = c_compiler + ['-shared',
                                '-fuse-ld=lld',
                                '-Wl,--no-undefined',
                                '-Wl,--version-script,python.exports',
                                '-o', str(python_dylib)] + objects + ['-Wl,-('] + libs + ['-Wl,-)']
            check_call(cmd, cwd=python_dist)
            check_call([cfg['CMAKE_STRIP'], python_dylib], cwd=python_dist)
        else:
            with open(python_dist / 'python.exports', 'w') as exports:
                exports.write('Py*\n_Py*\n__Py*\n')

            python_dylib = output / 'lib' / f'libpython{major}{minor}.dylib'
            cmd = c_compiler + ['-shared',
                                '-Wl,-exported_symbols_list,python.exports',
                                '-o', str(python_dylib)] + objects + libs
            check_call(cmd, cwd=python_dist)
        return (python_dist / 'install' / 'include' / f'python{major}.{minor}'), python_dylib

    else:
        assert target_os == 'Windows'
        python_dll = python_dist / manifest['build_info']['core']['shared_lib']
        (output / 'bin').mkdir(exist_ok=True)
        shutil.copy(python_dll, output / 'bin')
        shutil.copy(python_dll.parent / 'python3.dll', output / 'bin')

        (output / 'DLLs').mkdir(exist_ok=True)
        for name, ext in included_ext.items():
            dylib = ext.get('shared_lib')
            if dylib:
                shutil.copy(python_dist / dylib, output / 'DLLs')
            for lib in ext.get('links', []):
                dylib = lib.get('path_dynamic')
                if dylib:
                    # https://github.com/indygreg/python-build-standalone/issues/379
                    if lib['name'] in ['libcrypto-1_1-x64', 'libssl-1_1-x64']:
                        dylib = dylib.replace('-1_1-x64', '-3-x64')
                    shutil.copy(python_dist / dylib, output / 'DLLs')
        return (python_dist / 'install' / 'include'), (python_dist / 'install' / 'libs' / f'python{major}{minor}.lib')
