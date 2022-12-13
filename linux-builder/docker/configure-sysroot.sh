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

apt-get install \
    libc6-dev \
    libc6-arm64-cross \
    libc6-armhf-cross \
    libgcc-6-dev \
    libgcc-6-dev:arm64 \
    libgcc-6-dev:armhf \
    libz-dev \
    libz-dev:arm64 \
    libz-dev:armhf \
    libedit-dev \
    libedit-dev:arm64 \
    libedit-dev:armhf \
    symlinks

# Convert absolute symlinks to relative
symlinks -rcs /

