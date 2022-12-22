wget -N https://github.com/llvm/llvm-project/releases/download/llvmorg-15.0.6/clang+llvm-15.0.6-x86_64-linux-gnu-ubuntu-18.04.tar.xz
wget -N https://github.com/llvm/llvm-project/releases/download/llvmorg-15.0.6/clang+llvm-15.0.6-aarch64-linux-gnu.tar.xz
wget -N https://github.com/llvm/llvm-project/releases/download/llvmorg-15.0.6/clang+llvm-15.0.6-armv7a-linux-gnueabihf.tar.xz
wget -N https://github.com/Kitware/CMake/releases/download/v3.23.1/cmake-3.23.1-linux-x86_64.sh

ln -f clang+llvm-15.0.6-x86_64-linux-gnu-ubuntu-18.04.tar.xz docker/clang.tar.xz
ln -f cmake-3.23.1-linux-x86_64.sh docker/cmake.sh

mkdir docker/crosslib
tar -xvf clang+llvm-15.0.6-aarch64-linux-gnu.tar.xz --strip-components=1 -C docker/crosslib \
    clang+llvm-15.0.6-aarch64-linux-gnu/include/aarch64-unknown-linux-gnu/c++ \
    clang+llvm-15.0.6-aarch64-linux-gnu/lib/aarch64-unknown-linux-gnu \
    clang+llvm-15.0.6-aarch64-linux-gnu/lib/clang
tar -xvf clang+llvm-15.0.6-armv7a-linux-gnueabihf.tar.xz --strip-components=1 -C docker/crosslib \
    clang+llvm-15.0.6-armv7a-linux-gnueabihf/include/armv7l-unknown-linux-gnueabihf/c++ \
    clang+llvm-15.0.6-armv7a-linux-gnueabihf/lib/armv7l-unknown-linux-gnueabihf \
    clang+llvm-15.0.6-armv7a-linux-gnueabihf/lib/clang
# Rename armv7l to armv7
mv docker/crosslib/lib/armv7l-unknown-linux-gnueabihf docker/crosslib/lib/armv7-unknown-linux-gnueabihf
mv docker/crosslib/lib/clang/15.0.6/lib/armv7l-unknown-linux-gnueabihf docker/crosslib/lib/clang/15.0.6/lib/armv7-unknown-linux-gnueabihf
mv docker/crosslib/include/armv7l-unknown-linux-gnueabihf docker/crosslib/include/armv7-unknown-linux-gnueabihf
