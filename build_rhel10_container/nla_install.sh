#!/bin/bash
# Install RHEL10 image for using rpmbuild

[ -e /usr/bin/microdnf ] && microdnf install -y python3 rpm-build python3-setuptools
[ -e /usr/bin/dnf ] && dnf install -y python3 rpm-build python3-setuptools
rpm -qa --last | grep setup
rpm -qa --last | grep rpm-build

cd /tmp
cp ./docker-entrypoint.sh /
chmod +x /docker-entrypoint.sh
