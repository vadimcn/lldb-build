FROM debian:bookworm-slim AS build

RUN apt-get update
RUN apt-get install \
    xz-utils

# Install clang
COPY clang.tar.xz /tmp/clang.tar.xz
RUN tar -xvf /tmp/clang.tar.xz --strip-components=1 -C /usr/local

# Remove unneeded files
RUN cd /usr/local/bin &&\
    rm bugpoint clang-[a-z]* mlir* clangd opt llc lli find-all-symbols modularize llvm-lto llvm-lto2 dsymutil llvm-c-test c-index-test &&\
    strip -s * || true
RUN cd /usr/local/lib && rm *.a *.bc

# Install cmake
COPY cmake.sh /tmp/cmake.sh
RUN bash /tmp/cmake.sh --skip-license --prefix=/usr/local

# --------------------------------------------------
FROM debian:bookworm-slim

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
    wget \
    curl
RUN apt-get update

# Copy stuff from the build image
COPY --from=build /usr/local /usr/local
# libc++ cross-libs
COPY crosslib /usr/local

RUN ln -s /usr/local/bin/clang /usr/bin/cc && ln -s /usr/local/bin/clang++ /usr/bin/c++
RUN echo "/usr/local/lib/x86_64-unknown-linux-gnu" > /etc/ld.so.conf.d/clang_libs.conf
RUN ldconfig

# Install node
RUN curl -sL https://deb.nodesource.com/setup_18.x | bash -
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
    file \
    git \
    libc6-dev \
    libpcre3-dev \
    libstdc++-11-dev \
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

# Sysroot with legacy libs
COPY stretch /stretch

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
RUN apt-get autoremove && \
    apt-get clean

RUN rm -rf /var/lib/apt/lists/* && \
    rm -rf /tmp/*
