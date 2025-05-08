#!/bin/bash
# This script is picked by the running container to do the actual RPM build.
# Do not run directly

distro=$(/usr/bin/awk -F: '/PLATFORM_ID/{print $2}' /etc/os-release | sed 's:"::g')
echo distro=$distro

/usr/bin/python3 setup.py clean bdist_rpm --release 0.${distro} --vendor NLA --package "$(getent passwd "${USER}" | awk -F: '{print $5}') <$USER@nla.gov.au>"

