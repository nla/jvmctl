#!/bin/bash
distro=$(/usr/bin/awk -F: '/PLATFORM_ID/{print $2}' /etc/os-release | sed 's:"::g')
echo distro=$distro
mkdir -p "dist.${distro}"
/usr/bin/python3 setup.py clean bdist_rpm --dist-dir "dist.${distro}" --distribution-name "${distro}"

