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

usage() {
    echo "Usage: $0 [--venv] [-h|--help]"
    echo
    echo "Build binary packages for dnsdiag utilities using PyInstaller"
    echo
    echo "Options:"
    echo "  --venv       Create and use a virtual environment for building"
    echo "  -h, --help   Show this help message"
    echo
    echo "This script will:"
    echo "  * Install required dependencies (pyinstaller and project requirements)"
    echo "  * Build standalone executables for dnsping, dnstraceroute, and dnseval"
    echo "  * Package the binaries with configuration files"
    echo "  * Create a compressed archive (tar.gz on Unix, zip on Windows)"
    echo
    exit 0
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
DDVER=$(grep __version__ dnsdiag/shared.py | awk -F\' '{print $2}')
[ -z "${DDVER}" ] && die "Failed to extract version number from dnsdiag/shared.py"
PKG_NAME="dnsdiag-${DDVER}.${PLATFORM}-${ARCH}-bin"
PKG_PATH="pkg/${PKG_NAME}"

msg "Starting to build dnsdiag package version ${DDVER} for ${PLATFORM}-${ARCH}"

## main

if [ $# -gt 0 ]; then
    case "$1" in
        --venv)
            msg "Initializing virtualenv"
            checkbin "virtualenv"
            virtualenv -q --clear .venv
            if [ -f .venv/bin/activate ]; then  # *nix
                . .venv/bin/activate
            elif [ -f .venv/Scripts/activate ]; then  # windows
                . .venv/Scripts/activate
            fi
            ;;
        -h|--help)
            usage
            ;;
        *)
            die "Unknown option: $1. Use -h or --help for usage information."
            ;;
    esac
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

msg "Verifying built binaries..."
for tool in dnsping dnstraceroute dnseval; do
    BINARY="${PKG_PATH}/${tool}"
    [ "${PLATFORM}" = "windows" ] && BINARY="${BINARY}.exe"

    if [ ! -f "${BINARY}" ]; then
        die "Binary not found: ${BINARY}"
    fi

    if [ ! -x "${BINARY}" ]; then
        die "Binary is not executable: ${BINARY}"
    fi

    msg "Testing ${tool}..."
    if ! "${BINARY}" --help > /dev/null 2>&1; then
        die "Binary failed to execute: ${BINARY}"
    fi
done
msg "All binaries verified successfully"

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
    COPYFILE_DISABLE=1 tar cf "${PKG_NAME}.tar" "${PKG_NAME}" || die "Failed to build archive (tar)"
    gzip -9f "${PKG_NAME}.tar"             || die "Failed to build archive (gzip)"
fi

rm -fr "${PKG_NAME}"
