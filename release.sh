#!/bin/bash

if [ -z "$RPM_REPO" ]; then
   echo 'Set RPM_REPO to the destination to write RPMs to' >&2
   exit 1
fi

set -e -u

temp=$(mktemp -d)
trap 'rm -Rv "$temp"' EXIT

(cd logduct && python setup.py clean bdist_rpm -d "$temp")
(cd jvmctl && python setup.py clean bdist_rpm -d "$temp")

if [ ! -z "${SRPM_REPO+x}" ]; then
    sudo mv -vi "$temp"/*.src.rpm "$SRPM_REPO"
fi

sudo mv -vi "$temp"/*.noarch.rpm "$RPM_REPO"
sudo createrepo "$RPM_REPO"
