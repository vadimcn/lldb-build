# Must be run as root, in order for debootstrap and chroot to work
set -ex

TARGET_DIR=stretch

# rm -rf $TARGET_DIR
# debootstrap --variant=minbase stretch $TARGET_DIR https://archive.debian.org/debian/

cat >$TARGET_DIR/configure-apt.sh <<EOF
export DEBIAN_FRONTEND=noninteractive

( echo 'quiet "true";'; \
  echo 'APT::Get::Assume-Yes "true";'; \
  echo 'APT::Install-Recommends "false";'; \
  echo 'Acquire::Check-Valid-Until "false";'; \
  echo 'Acquire::Retries "5";'; \
) > /etc/apt/apt.conf.d/99-builder

dpkg --add-architecture armhf
dpkg --add-architecture arm64
apt-get update
apt-get install symlinks
EOF

# Unfortunately some of these libs conflict between architectures, so we have to install them one-by-one
cat >$TARGET_DIR/install-x64.sh <<EOF
apt-get install \
    libc6-dev \
    libgcc-6-dev \
    libstdc++-6-dev \
    zlib1g-dev \
    libzstd-dev \
    libedit-dev
# Convert absolute symlinks to relative
symlinks -rcs /
EOF

cat >$TARGET_DIR/install-arm64.sh <<EOF
apt-get install \
    libc6-arm64-cross \
    libgcc-6-dev:arm64 \
    libstdc++-6-dev:arm64 \
    zlib1g-dev:arm64 \
    libzstd-dev:arm64 \
    libedit-dev:arm64 \
# Convert absolute symlinks to relative
symlinks -rcs /
EOF

cat >$TARGET_DIR/install-arm.sh <<EOF
apt-get install \
    libc6-armhf-cross \
    libgcc-6-dev:armhf \
    libstdc++-6-dev:armhf \
    zlib1g-dev:armhf \
    libzstd-dev:armhf \
    libedit-dev:armhf
# Convert absolute symlinks to relative
symlinks -rcs /
EOF

chmod +x $TARGET_DIR/*.sh

# chroot $TARGET_DIR bash
