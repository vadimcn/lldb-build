#!/usr/bin/env python3
'''Create a Debian sysroot for cross-building.

The script downloads the requested packages for amd64, arm64 and armhf, unpacks
all their contents into a single sysroot directory, and rewrites absolute
symlinks to be relative so they remain valid when the sysroot is relocated.
'''

import argparse
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Optional


MIRROR = 'https://archive.debian.org/debian'
SEC_MIRROR = 'https://archive.debian.org/debian-security'

DISTRO = 'stretch'
PACKAGES = [
    'libc6-dev',
    'libgcc-6-dev',
    'zlib1g-dev',

    'libc6-arm64-cross',
    'libgcc-6-dev:arm64',
    'zlib1g-dev:arm64',

    'libc6-armhf-cross',
    'libgcc-6-dev:armhf',
    'zlib1g-dev:armhf',
    'libatomic1:armhf',
]

# LLVM needs some packages to be newer
DISTRO2 = 'bullseye'
PACKAGES2 = [
    'libzstd-dev',
    'libzstd-dev:arm64',
    'libzstd-dev:armhf',
    'libzstd1',
    'libzstd1:arm64',
    'libzstd1:armhf',
]


def run(cmd: List[str], env: Optional[Dict[str, str]] = None) -> None:
    subprocess.run(cmd, check=True, env=env)


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def write_preferences(temp_root: Path) -> None:
    entries: List[str] = [
        'Package: *\n'
        f'Pin: release n={DISTRO}\n'
        'Pin-Priority: 900\n',
    ]
    for pkg in PACKAGES2:
        entries.append(
            f'Package: {pkg}\n'
            f'Pin: release n={DISTRO2}\n'
            'Pin-Priority: 950\n'
        )
    write_file(temp_root / 'etc/apt/preferences', '\n'.join(entries) + '\n')


def configure_apt(temp_root: Path) -> List[str]:
    # Ensure apt directory structure exists before writing configuration.
    (temp_root / 'etc/apt').mkdir(parents=True, exist_ok=True)
    (temp_root / 'etc/apt/sources.list.d').mkdir(parents=True, exist_ok=True)
    (temp_root / 'etc/apt/preferences.d').mkdir(parents=True, exist_ok=True)
    (temp_root / 'etc/preferences.d').mkdir(parents=True, exist_ok=True)
    (temp_root / 'state/lists/partial').mkdir(parents=True, exist_ok=True)
    (temp_root / 'cache/archives/partial').mkdir(parents=True, exist_ok=True)
    status_file = temp_root / 'state/status'
    status_file.parent.mkdir(parents=True, exist_ok=True)
    if not status_file.exists():
        status_file.write_text('')

    write_file(
        temp_root / 'etc/apt/apt.conf',
        f'Dir "{temp_root}";\n'
        f'Dir::Cache "{temp_root / 'cache'}";\n'
        f'Dir::State "{temp_root / 'state'}";\n'
        f'Dir::Etc "{temp_root / 'etc'}";\n'
        'Dir::State::status "status";\n'
        'Dir::Etc::sourcelist "apt/sources.list";\n'
        'Dir::Etc::sourceparts "apt/sources.list.d";\n'
        'Dir::Etc::main "apt/apt.conf";\n'
        'Dir::Etc::preferences "apt/preferences";\n'
        'Dir::Etc::preferencesparts "apt/preferences.d";\n'
        'Acquire::Check-Valid-Until "false";\n'
        'Acquire::Retries "5";\n'
        'Acquire::AllowInsecureRepositories "true";\n'
        'Acquire::AllowDowngradeToInsecureRepositories "true";\n'
        'APT::Get::Assume-Yes "true";\n'
        'APT::Get::AllowUnauthenticated "true";\n'
        'APT::Install-Recommends "false";\n'
        'APT::Architectures {\n'
        '    "amd64";\n'
        '    "arm64";\n'
        '    "armhf";\n'
        '};\n'
        'Debug::NoLocking "true";\n',
    )

    write_file(
        temp_root / 'etc/apt/sources.list',
        '\n'.join(
            [
                f'deb [arch=amd64,arm64,armhf] {MIRROR} {DISTRO} main',
                f'deb [arch=amd64,arm64,armhf] {SEC_MIRROR} {DISTRO}/updates main',
                f'deb [arch=amd64,arm64,armhf] {MIRROR} {DISTRO2} main',
            ]
        )
        + '\n',
    )

    write_preferences(temp_root)

    apt_get = [
        'apt-get',
        '-o', f'Dir={temp_root}',
        '-o', f'Dir::Cache={temp_root / 'cache'}',
        '-o', f'Dir::State={temp_root / 'state'}',
        '-o', f'Dir::Etc={temp_root / 'etc'}',
        '-o', 'Debug::NoLocking=1',
        '-c', str(temp_root / 'etc/apt/apt.conf'),
    ]

    run(apt_get + ['update'])
    return apt_get


def download_packages(apt_get: List[str], packages: Iterable[str]) -> None:
    pkgs = [pkg for pkg in packages if pkg]
    if pkgs:
        run(apt_get + ['--download-only', 'install', *pkgs])


def extract_packages(temp_root: Path, sysroot_dir: Path) -> None:
    if sysroot_dir.exists():
        shutil.rmtree(sysroot_dir)
    sysroot_dir.mkdir(parents=True, exist_ok=True)

    debs = sorted((temp_root / 'cache/archives').glob('*.deb'))
    for deb in debs:
        run(['dpkg-deb', '-x', str(deb), str(sysroot_dir)])


def rewrite_symlinks(sysroot_dir: Path) -> None:
    for path in sysroot_dir.rglob('*'):
        if path.is_symlink():
            target = os.readlink(path)
            if target.startswith('/'):
                absolute_target = sysroot_dir / target.lstrip('/')
                if absolute_target.exists():
                    relative_target = os.path.relpath(absolute_target, path.parent)
                    path.unlink()
                    path.symlink_to(relative_target)


def build_sysroot(temp_root: Path, sysroot_dir: Path):
    apt_get = configure_apt(temp_root)
    download_packages(apt_get, PACKAGES + PACKAGES2)
    extract_packages(temp_root, sysroot_dir)
    rewrite_symlinks(sysroot_dir)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create a Debian sysroot for cross-building.')
    parser.add_argument('-o', '--output', type=Path, required=True)
    args = parser.parse_args()
    temp_root = Path.cwd() / 'sysroot-temp'
    temp_root.mkdir(parents=True, exist_ok=True)
    build_sysroot(temp_root, args.output)
    run(['tar', '--zstd', '-cf', str(args.output.with_suffix('.tar.zst')), '-C', str(args.output), '.'])
    print(f'Sysroot created at {args.output}')
