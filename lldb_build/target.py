from typing import Dict, TypedDict, Literal
import copy


class RequiredTargetConfig(TypedDict, total=True):
    CMAKE_HOST_SYSTEM_NAME: Literal['Linux', 'Darwin', 'Windows']
    CMAKE_HOST_SYSTEM_PROCESSOR: str
    CMAKE_SYSTEM_NAME: Literal['Linux', 'Darwin', 'Windows']
    CMAKE_SYSTEM_PROCESSOR: str
    CMAKE_C_COMPILER: str
    CMAKE_CXX_COMPILER: str
    CMAKE_C_FLAGS: str
    CMAKE_CXX_FLAGS: str
    CMAKE_STRIP: str


class TargetConfig(RequiredTargetConfig, total=False):
    TARGET_PYTHON_ARCHIVE: str
    CMAKE_OSX_ARCHITECTURES: str
    CMAKE_CXX_STANDARD_LIBRARIES: str
    CMAKE_EXE_LINKER_FLAGS: str
    CMAKE_SHARED_LINKER_FLAGS: str
    CMAKE_SYSROOT: str


def update_cfg(original: TargetConfig, updates: Dict[str, str]) -> TargetConfig:
    result = copy.deepcopy(original)
    result.update(updates)  # type: ignore
    return result


linux: TargetConfig = {
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


darwin: TargetConfig = {
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

windows: TargetConfig = {
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

targets: Dict[str, TargetConfig] = {
    'x86_64-linux-gnu': update_cfg(linux, {
        'CMAKE_SYSTEM_PROCESSOR': 'x86_64',
        'CMAKE_C_FLAGS': '-target x86_64-linux-gnu ' + linux['CMAKE_C_FLAGS'],
        'CMAKE_CXX_FLAGS': '-target x86_64-linux-gnu ' + linux['CMAKE_CXX_FLAGS'],
        'CMAKE_CXX_STANDARD_LIBRARIES': '-rtlib=compiler-rt ' + linux['CMAKE_CXX_STANDARD_LIBRARIES'],
    }),
    'aarch64-linux-gnu': update_cfg(linux, {
        'TARGET_PYTHON_ARCHIVE': 'cpython-*-aarch64-*-linux-*.tar.zst',
        'CMAKE_SYSTEM_PROCESSOR': 'aarch64',
        'CMAKE_C_FLAGS': '-target aarch64-linux-gnu ' + linux['CMAKE_C_FLAGS'],
        'CMAKE_CXX_FLAGS': '-target aarch64-linux-gnu ' + linux['CMAKE_CXX_FLAGS'],
        'CMAKE_CXX_STANDARD_LIBRARIES': '-rtlib=compiler-rt ' + linux['CMAKE_CXX_STANDARD_LIBRARIES'],
        'LLVM_HOST_TRIPLE': 'aarch64-linux-gnu',
        'LLVM_TARGET_ARCH': 'aarch64',
    }),
    'arm-linux-gnueabihf': update_cfg(linux, {
        'TARGET_PYTHON_ARCHIVE': 'cpython-*-arm*-linux-*.tar.zst',
        'CMAKE_SYSTEM_PROCESSOR': 'arm',
        'CMAKE_C_FLAGS': '-target armv7-linux-gnueabihf ' + linux['CMAKE_C_FLAGS'],
        'CMAKE_CXX_FLAGS': '-target armv7-linux-gnueabihf ' + linux['CMAKE_CXX_FLAGS'],
        'LLVM_HOST_TRIPLE': 'arm-linux-gnueabihf',
        'LLVM_TARGET_ARCH': 'arm',
    }),
    'x86_64-apple-darwin': update_cfg(darwin, {
        'CMAKE_OSX_ARCHITECTURES': 'x86_64',
        'CMAKE_SYSTEM_VERSION': '11.0.0',
    }),
    'aarch64-apple-darwin': update_cfg(darwin, {
        'TARGET_PYTHON_ARCHIVE': 'cpython-*-aarch64-*-darwin-*.tar.zst',
        'CMAKE_SYSTEM_PROCESSOR': 'arm64',
        'CMAKE_OSX_ARCHITECTURES': 'arm64',
        'CMAKE_SYSTEM_VERSION': '20.0.0',
        'LLVM_HOST_TRIPLE': 'arm64-apple-darwin',
        'LLVM_TARGET_ARCH': 'arm64',
    }),
    'x86_64-windows-msvc': update_cfg(windows, {})
}


def get_target_config(target_triple: str) -> TargetConfig:
    cfg = targets.get(target_triple)
    if cfg is not None:
        return cfg
    raise KeyError('Unsupported target triple:', target_triple)
