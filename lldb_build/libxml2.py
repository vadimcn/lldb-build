from pathlib import Path
from subprocess import check_call

from .utils import dict_to_cmake, out_of_date
from .target import TargetConfig


def build_libxml2(work_dir: Path, cfg: TargetConfig, build_type: str):
    libxml2_src = Path(__file__).resolve().parent.parent / 'libxml2'
    libxml2_build = work_dir / 'libxml2'
    libxml2_build.mkdir(exist_ok=True)
    libxml2_install = work_dir / 'libxml2' / 'install'
    if cfg['CMAKE_SYSTEM_NAME'] != 'Windows':
        libname = 'libxml2.a'
    else:
        libname = 'libxml2sd.lib' if build_type == 'Debug' else 'libxml2s.lib'
    libxml2_lib = libxml2_install / 'lib' / libname

    if out_of_date([libxml2_lib], [libxml2_src / '*.c', libxml2_src / '*.h']):
        cmake_args = {
            'CMAKE_BUILD_TYPE': build_type,
            'CMAKE_INSTALL_PREFIX': str(libxml2_install),
            'BUILD_SHARED_LIBS': 'OFF',
            'LIBXML2_WITH_SAX1': 'ON',
            'LIBXML2_WITH_THREADS': 'ON',
            # off
            'LIBXML2_WITH_C14N': 'OFF',
            'LIBXML2_WITH_CATALOG': 'OFF',
            'LIBXML2_WITH_DEBUG': 'OFF',
            'LIBXML2_WITH_FTP': 'OFF',
            'LIBXML2_WITH_HTML': 'OFF',
            'LIBXML2_WITH_HTTP': 'OFF',
            'LIBXML2_WITH_ICONV': 'OFF',
            'LIBXML2_WITH_ICU': 'OFF',
            'LIBXML2_WITH_ISO8859X': 'OFF',
            'LIBXML2_WITH_LEGACY': 'OFF',
            'LIBXML2_WITH_LZMA': 'OFF',
            'LIBXML2_WITH_MEM_DEBUG': 'OFF',
            'LIBXML2_WITH_MODULES': 'OFF',
            'LIBXML2_WITH_OUTPUT': 'OFF',
            'LIBXML2_WITH_PATTERN': 'OFF',
            'LIBXML2_WITH_PROGRAMS': 'OFF',
            'LIBXML2_WITH_PUSH': 'OFF',
            'LIBXML2_WITH_PYTHON': 'OFF',
            'LIBXML2_WITH_READER': 'OFF',
            'LIBXML2_WITH_REGEXPS': 'OFF',
            'LIBXML2_WITH_SCHEMAS': 'OFF',
            'LIBXML2_WITH_SCHEMATRON': 'OFF',
            'LIBXML2_WITH_TESTS': 'OFF',
            'LIBXML2_WITH_THREAD_ALLOC': 'OFF',
            'LIBXML2_WITH_TREE': 'OFF',
            'LIBXML2_WITH_VALID': 'OFF',
            'LIBXML2_WITH_WRITER': 'OFF',
            'LIBXML2_WITH_XINCLUDE': 'OFF',
            'LIBXML2_WITH_XPATH': 'OFF',
            'LIBXML2_WITH_XPTR': 'OFF',
            'LIBXML2_WITH_ZLIB': 'OFF',
        }
        cmake_args.update(cfg)  # type: ignore

        cmake_args = dict_to_cmake(cmake_args)
        print('Configuring XML2 with:')
        for a in cmake_args:
            print(' ', a)

        check_call(['cmake', '-GNinja', str(libxml2_src), '-B', str(libxml2_build)] + cmake_args)
        check_call(['cmake', '--build', str(libxml2_build)])
        check_call(['cmake', '--build', str(libxml2_build), '--target', 'install'])

    return (libxml2_install / 'include/libxml2'), libxml2_lib
