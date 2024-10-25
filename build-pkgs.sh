#!/bin/sh

set -e

## display an error message and exit(1)
die() {
    echo "[ERROR]  $*" 1>&2
    exit 1
}

msg() {
    echo "[STATUS] $*" 1>&2
}

checkbin() {
    which "${1}" > /dev/null 2>&1 || die "${1} is not installed"
}

## validate required tools
checkbin "python3"

## constants
if [ "Windows_NT" = "${OS}" ]; then ## windows compatibility shims
  PLATFORM='windows'
else
  PLATFORM=$(uname -s | tr 'A-Z' 'a-z')
fi
ARCH=$(uname -m)
DDVER=$(grep version util/shared.py | awk -F\' '{print $2}')
PKG_NAME="dnsdiag-${DDVER}.${PLATFORM}-${ARCH}-bin"
PKG_PATH="pkg/${PKG_NAME}"

msg "Starting to build dnsdiag package version ${DDVER} for ${PLATFORM}-${ARCH}"

## main

if [ $# -gt 0 ]; then
    if [ "$1" = "--venv" ]; then
        msg "Initializing virtualenv"
        checkbin "virtualenv"
        virtualenv -q --clear .venv
        if [ -f .venv/bin/activate ]; then  # *nix
            . .venv/bin/activate
        elif [ -f .venv/Scripts/activate ]; then  # windows
            . .venv/Scripts/activate
        fi
    fi
fi

msg "Installing dependencies"
pip3 install --upgrade pip
pip3 install -q pyinstaller || die "Failed to install pyinstaller"
pip3 install -q -r requirements.txt || die "Failed to install dependencies"

mkdir -p "${PKG_PATH}" || die "Cannot create dir hierarcy: ${PKG_PATH}"

for i in dnsping.py dnstraceroute.py dnseval.py; do
    msg "Building package for ${i}"
    pyinstaller ${i} -y --onefile --clean \
        --log-level=ERROR \
        --distpath="${PKG_PATH}" \
        --hidden-import=dns \
        --hidden-import=httpx
done

msg "Adding extra files..."
for i in public-servers.txt public-v4.txt rootservers.txt; do
    cp ${i} "${PKG_PATH}/"
done

cd pkg
if [ "${PLATFORM:-}" = "windows" ]; then
    msg "Creating archive: ${PKG_NAME}.zip"
    powershell Compress-Archive -Force "${PKG_NAME}" "${PKG_NAME}.zip"
 else
    msg "Creating tarball: ${PKG_NAME}.tar.gz"
    tar cf "${PKG_NAME}.tar" "${PKG_NAME}" || die "Failed to build archive (tar)"
    gzip -9f "${PKG_NAME}.tar"             || die "Failed to build archive (gzip)"
fi

rm -fr "${PKG_NAME}"
