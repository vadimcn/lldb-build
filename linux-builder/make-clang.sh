set -ex

rm -rf clang
mkdir clang

tar -xvf clang+llvm-15.0.6-x86_64-linux-gnu-ubuntu-18.04.tar.xz --strip-components=1 -C clang

# Remove unneeded stuff
(cd clang/bin && rm bugpoint clang-[a-z]* mlir* clangd opt llc lli find-all-symbols modularize llvm-lto llvm-lto2 dsymutil llvm-c-test c-index-test &&
    strip -s * || true)
(cd clang/lib && rm *.a *.bc)

tar -xvf clang+llvm-15.0.6-aarch64-linux-gnu.tar.xz --strip-components=1 -C clang \
    clang+llvm-15.0.6-aarch64-linux-gnu/include/aarch64-unknown-linux-gnu/c++ \
    clang+llvm-15.0.6-aarch64-linux-gnu/lib/aarch64-unknown-linux-gnu \
    clang+llvm-15.0.6-aarch64-linux-gnu/lib/clang

tar -xvf clang+llvm-15.0.6-armv7a-linux-gnueabihf.tar.xz --strip-components=1 -C clang\
    clang+llvm-15.0.6-armv7a-linux-gnueabihf/include/armv7l-unknown-linux-gnueabihf/c++ \
    clang+llvm-15.0.6-armv7a-linux-gnueabihf/lib/armv7l-unknown-linux-gnueabihf \
    clang+llvm-15.0.6-armv7a-linux-gnueabihf/lib/clang

tar --zstd -cf clang-15.tar.zst -C clang .
