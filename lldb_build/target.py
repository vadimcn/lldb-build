from typing import Dict

linux = {
    'CMAKE_HOST_SYSTEM_NAME': 'Linux',
    'CMAKE_HOST_SYSTEM_PROCESSOR': 'x86_64',
    'CMAKE_SYSTEM_NAME': 'Linux',
    'CMAKE_SYSTEM_PROCESSOR': '???',
    'CMAKE_CXX_COMPILER': 'clang++',
    'CMAKE_C_COMPILER': 'clang',
    'CMAKE_CXX_FLAGS': '-fPIC -stdlib=libc++ -nostdlib++',
    'CMAKE_C_FLAGS': '-fPIC',
    'CMAKE_STRIP': 'llvm-strip',
    'CMAKE_CXX_STANDARD_LIBRARIES': '-l:libc++.a -l:libc++abi.a -l:libunwind.a',
    'CMAKE_EXE_LINKER_FLAGS': '-fuse-ld=lld',
    'CMAKE_SHARED_LINKER_FLAGS': '-fuse-ld=lld',
}

darwin = {
    'CMAKE_HOST_SYSTEM_NAME': 'Darwin',
    'CMAKE_HOST_SYSTEM_PROCESSOR': 'x86_64',
    'CMAKE_SYSTEM_NAME': 'Darwin',
    'CMAKE_SYSTEM_PROCESSOR': '???',
    'CMAKE_CXX_COMPILER': 'clang++',
    'CMAKE_C_COMPILER': 'clang',
    'CMAKE_CXX_FLAGS': '',
    'CMAKE_C_FLAGS': '',
    'CMAKE_STRIP': 'strip',
}

windows = {
    'CMAKE_HOST_SYSTEM_NAME': 'Windows',
    'CMAKE_HOST_SYSTEM_PROCESSOR': 'x86_64',
    'CMAKE_SYSTEM_NAME': 'Windows',
    'CMAKE_SYSTEM_PROCESSOR': 'x86_64',
    'CMAKE_C_COMPILER': 'cl',
    'CMAKE_CXX_COMPILER': 'cl',
    'CMAKE_CXX_FLAGS': '',
    'CMAKE_C_FLAGS': '',
    'CMAKE_STRIP': '',
}

targets: Dict[str, Dict[str, str]] = {
    'x86_64-linux-gnu': {
        **linux,
        'CMAKE_SYSTEM_PROCESSOR': 'x86_64',
        'CMAKE_CXX_STANDARD_LIBRARIES': '-rtlib=compiler-rt ' + linux['CMAKE_CXX_STANDARD_LIBRARIES'],
    },
    'aarch64-linux-gnu': {
        **linux,
        'TARGET_PYTHON_ARCHIVE': 'cpython-*-aarch64-*-linux-*.tar.zst',
        'CMAKE_SYSTEM_PROCESSOR': 'aarch64',
        'CMAKE_CXX_STANDARD_LIBRARIES': '-rtlib=compiler-rt ' + linux['CMAKE_CXX_STANDARD_LIBRARIES'],
        'LLVM_HOST_TRIPLE': 'aarch64-linux-gnu',
        'LLVM_TARGET_ARCH': 'aarch64',
    },
    'arm-linux-gnueabihf': {
        **linux,
        'TARGET_PYTHON_ARCHIVE': 'cpython-*-arm*-linux-*.tar.zst',
        'CMAKE_SYSTEM_PROCESSOR': 'arm',
        'LLVM_HOST_TRIPLE': 'armv7-linux-gnueabihf',
        'LLVM_TARGET_ARCH': 'arm',
    },
    'x86_64-apple-darwin': {
        **darwin,
        'CMAKE_OSX_ARCHITECTURES': 'x86_64',
        'CMAKE_SYSTEM_VERSION': '11.0.0',
    },
    'aarch64-apple-darwin': {
        **darwin,
        'TARGET_PYTHON_ARCHIVE': 'cpython-*-aarch64-*-darwin-*.tar.zst',
        'CMAKE_SYSTEM_PROCESSOR': 'arm64',
        'CMAKE_OSX_ARCHITECTURES': 'arm64',
        'CMAKE_SYSTEM_VERSION': '20.0.0',
        'LLVM_HOST_TRIPLE': 'arm64-apple-darwin',
        'LLVM_TARGET_ARCH': 'arm64',
    },
    'x86_64-windows-msvc': windows,
}


def get_target_config(target_triple: str) -> Dict[str, str]:
    cfg = targets.get(target_triple)
    if cfg is not None:
        host_triple = cfg.get('LLVM_HOST_TRIPLE')
        if host_triple:
            cfg = {
                **cfg,
                'CMAKE_C_COMPILER_TARGET': host_triple,
                'CMAKE_CXX_COMPILER_TARGET': host_triple,
            }
        return cfg
    raise KeyError('Unsupported target triple:', target_triple)
