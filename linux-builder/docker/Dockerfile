FROM debian:buster-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN groupadd -g 1000 build && \
    useradd -u 1000 -g 1000 -m build -d /build -s /bin/bash -G sudo && \
    passwd -d build && \
    mkdir /tools && \
    chown -R build:build /build /tools

CMD ["/bin/bash", "--login"]

RUN ( echo 'quiet "true";'; \
      echo 'APT::Get::Assume-Yes "true";'; \
      echo 'APT::Install-Recommends "false";'; \
      echo 'Acquire::Check-Valid-Until "false";'; \
      echo 'Acquire::Retries "5";'; \
    ) > /etc/apt/apt.conf.d/99-builder

RUN apt-get update
RUN apt-get install \
    ca-certificates \
    apt-transport-https \
    sudo \
    binutils \
    xz-utils \
    wget \
    curl

RUN apt-get update

# Install clang
COPY clang.tar.xz /tmp/clang.tar.xz
RUN tar -xvf /tmp/clang.tar.xz --strip-components=1 -C /usr/local
# libc++ cross-libs
COPY crosslib /usr/local
# Remove unneeded files
RUN cd /usr/local/bin &&\
    rm bugpoint clang-[a-z]* mlir* clangd opt llc lli find-all-symbols modularize llvm-lto llvm-lto2 dsymutil llvm-c-test c-index-test &&\
    strip -s * || true
RUN cd /usr/local/lib && rm *.a *.bc
RUN ln -s /usr/local/bin/clang /usr/bin/cc && ln -s /usr/local/bin/clang++ /usr/bin/c++

# Install cmake
COPY cmake.sh /tmp/cmake.sh
RUN bash /tmp/cmake.sh --skip-license --prefix=/usr/local

# Install node
RUN curl -sL https://deb.nodesource.com/setup_14.x | bash -
RUN apt-get install nodejs

# Install rustup
ENV RUSTUP_HOME=/opt/rust/rustup \
    CARGO_HOME=/opt/rust/cargo \
    PATH=$PATH:/opt/rust/cargo/bin
RUN curl https://sh.rustup.rs -sSf | sh -s -- -v -y --profile minimal --default-toolchain none \
    && chmod -R a+w $RUSTUP_HOME $CARGO_HOME

# Build tools
RUN apt-get install \
    automake \
    binutils \
    bison \
    debootstrap \
    file \
    git \
    libc6-dev \
    libpcre3-dev \
    libstdc++-8-dev \
    libtinfo5 \
    libz-dev \
    make \
    ncdu \
    ninja-build \
    python3 \
    swig \
    unzip \
    xz-utils \
    zip \
    zstd

# Create sysroot with legacy libs
RUN debootstrap --variant=minbase stretch /tmp/stretch
COPY configure-sysroot.sh /tmp/stretch/configure-sysroot.sh
RUN chroot /tmp/stretch /configure-sysroot.sh
RUN mkdir /stretch && \
    mv /tmp/stretch/lib /stretch/lib && \
    mv /tmp/stretch/usr /stretch/usr

# Update headers which LLDB needs in order to compile for arm64
COPY ptrace.h      /stretch/usr/include/aarch64-linux-gnu/asm/ptrace.h
COPY sigcontext.h  /stretch/usr/include/aarch64-linux-gnu/asm/sigcontext.h
COPY sve_context.h /stretch/usr/include/aarch64-linux-gnu/asm/sve_context.h

# Defult to ld.gold
RUN update-alternatives --install "/usr/bin/ld" "ld" "/usr/bin/ld.gold" 20 && \
    update-alternatives --install "/usr/bin/ld" "ld" "/usr/bin/ld.bfd" 10

# Configure linker for cargo
ENV CARGO_TARGET_X86_64_UNKNOWN_LINUX_GNU_LINKER=clang \
    CARGO_TARGET_X86_64_UNKNOWN_LINUX_GNU_RUSTFLAGS="-Clink-arg=--sysroot=/stretch -Clink-arg=-fuse-ld=lld -Clink-arg=--target=x86_64-unknown-linux-gnu" \
    CARGO_TARGET_ARMV7_UNKNOWN_LINUX_GNUEABIHF_LINKER=clang \
    CARGO_TARGET_ARMV7_UNKNOWN_LINUX_GNUEABIHF_RUSTFLAGS="-Clink-arg=--sysroot=/stretch -Clink-arg=-fuse-ld=lld -Clink-arg=--target=armv7-unknown-linux-gnueabihf" \
    CARGO_TARGET_AARCH64_UNKNOWN_LINUX_GNU_LINKER=clang \
    CARGO_TARGET_AARCH64_UNKNOWN_LINUX_GNU_RUSTFLAGS="-Clink-arg=--sysroot=/stretch -Clink-arg=-fuse-ld=lld -Clink-arg=--target=aarch64-unknown-linux-gnu"

# Cleanup
RUN apt-get remove debootstrap && \
    apt-get autoremove && \
    apt-get clean

RUN rm -rf /var/lib/apt/lists/* && \
    rm -rf /tmp/*
