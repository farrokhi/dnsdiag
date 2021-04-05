#!/bin/sh

set -e
set -u

## display an error message and exit(1)
die() {
    echo "ERROR: $*" 1>&2
    exit 1
}

## validate required tools
which -s upx     || die "upx is not installed"
which -s python3 || die "python3 is not installed"
which -s pip3    || die "pip3 is not installed"

## constants
ARCH=`uname -m`
PLATFORM=`uname -s | tr 'A-Z' 'a-z'`
DDVER=`grep version setup.py | awk -F\" '{print $2}'`
PKG_NAME="dnsdiag-${DDVER}.${PLATFORM}-${ARCH}-bin"
PKG_PATH="pkg/${PKG_NAME}"

## main
echo "Building package for ${PLATFORM}-${ARCH} under ${PKG_PATH}"
echo
pip3 install pyinstaller || die "Failed to install pyinstaller"
pip3 install -r requirements.txt || die "Failed to install dependencies"

mkdir -p ${PKG_PATH} || die "Cannot create dir hierarcy: ${PKG_PATH}"

for i in dnsping.py dnstraceroute.py dnseval.py; do
    pyinstaller ${i} -y --onefile --clean \
        --log-level=ERROR \
        --distpath=${PKG_PATH} \
        --hidden-import=dnspython \
        --hidden-import=requests
done

for i in public-servers.txt public-v4.txt rootservers.txt; do
    cp -v ${i} ${PKG_PATH}/
done

## build the tarball
cd pkg
tar cvf ${PKG_NAME}.tar ${PKG_NAME} || die "Failed to build archive (tar)"
gzip -9v ${PKG_NAME}.tar            || die "Failed to build archive (gzip)"
rm -fr ${PKG_NAME}
