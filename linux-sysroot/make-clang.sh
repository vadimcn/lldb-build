set -ex

SCRATCH_DIR=clang

wget -N https://github.com/llvm/llvm-project/releases/download/llvmorg-15.0.6/clang+llvm-15.0.6-x86_64-linux-gnu-ubuntu-18.04.tar.xz
wget -N https://github.com/llvm/llvm-project/releases/download/llvmorg-15.0.6/clang+llvm-15.0.6-aarch64-linux-gnu.tar.xz
wget -N https://github.com/llvm/llvm-project/releases/download/llvmorg-15.0.6/clang+llvm-15.0.6-armv7a-linux-gnueabihf.tar.xz

rm -rf $SCRATCH_DIR
mkdir $SCRATCH_DIR

tar -xvf clang+llvm-15.0.6-x86_64-linux-gnu-ubuntu-18.04.tar.xz --strip-components=1 -C $SCRATCH_DIR

# Remove unneeded stuff
(cd $SCRATCH_DIR/bin && rm bugpoint clang-[a-z]* mlir* clangd opt llc lli find-all-symbols modularize llvm-lto llvm-lto2 dsymutil llvm-c-test c-index-test &&
    strip -s * || true)
(cd $SCRATCH_DIR/lib && rm *.a *.bc)

tar -xvf clang+llvm-15.0.6-aarch64-linux-gnu.tar.xz --strip-components=1 -C $SCRATCH_DIR \
    clang+llvm-15.0.6-aarch64-linux-gnu/include/aarch64-unknown-linux-gnu/c++ \
    clang+llvm-15.0.6-aarch64-linux-gnu/lib/aarch64-unknown-linux-gnu \
    clang+llvm-15.0.6-aarch64-linux-gnu/lib/clang

tar -xvf clang+llvm-15.0.6-armv7a-linux-gnueabihf.tar.xz --strip-components=1 -C $SCRATCH_DIR\
    clang+llvm-15.0.6-armv7a-linux-gnueabihf/include/armv7l-unknown-linux-gnueabihf/c++ \
    clang+llvm-15.0.6-armv7a-linux-gnueabihf/lib/armv7l-unknown-linux-gnueabihf \
    clang+llvm-15.0.6-armv7a-linux-gnueabihf/lib/clang

Rename armv7l to armv7
mv $SCRATCH_DIR/lib/armv7l-unknown-linux-gnueabihf $SCRATCH_DIR/lib/armv7-unknown-linux-gnueabihf
mv $SCRATCH_DIR/lib/clang/15.0.6/lib/armv7l-unknown-linux-gnueabihf $SCRATCH_DIR/lib/clang/15.0.6/lib/armv7-unknown-linux-gnueabihf
mv $SCRATCH_DIR/include/armv7l-unknown-linux-gnueabihf $SCRATCH_DIR/include/armv7-unknown-linux-gnueabihf

tar --zstd -cf clang-15.tar.zst -C clang .
