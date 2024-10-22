The goal here is to build a Docker container containing clang toolchain capable of building LLDB for x86_64, arm64 and armhf architectures
for the Debian verstion we are targetting (Stretch currently).

download.sh      - Download a recent clang toolchain for all architectures, unpack arch libs into appropriate locations.
make-systroot.sh - Bootstrap Debian sysroot, from which libs that we need for building LLDB can be pulled into the Docker image.
build.sh         - Build the image.
