#!/bin/bash
# WARNING: This script is designed to run the container in rootless mode (ie: as the user running the script)

OS_VER=8
Default='\e[0m';Red='\e[31m';Green='\e[32m';Yellow='\e[33m';Cyan='\e[36m';LBlue='\e[94m'
script_dir=$(dirname $(readlink -f $0))
cd "${script_dir}"

id=$(/usr/bin/id -u)
[ "${id}" == "0" ] && { echo -e '${Red}DO NOT run as root.${Default}'; exit 1; }

name=$(/usr/bin/awk -F'"' '/ name /{print $2}' setup.py)
version=$(/usr/bin/awk -F'"' '/ version /{print $2}' setup.py)
RPM_NAME="${name}-${version}-0.el${OS_VER}.noarch.rpm"

/usr/bin/rm -rf /tmp/${USER}_rpmbuild
/usr/bin/mkdir -p /tmp/${USER}_rpmbuild
/usr/bin/rsync -a --delete * /tmp/${USER}_rpmbuild/
/usr/bin/podman run --userns=keep-id -v /tmp/${USER}_rpmbuild:/tmp/rpmbuild:Z --replace --name=rpmbuild${OS_VER} localhost/rpmbuild${OS_VER} >/tmp/${USER}_rpmbuild${OS_VER}.txt 2>&1

RPM=$(/usr/bin/ls /tmp/${USER}_rpmbuild/dist/${RPM_NAME} 2>/dev/null)
[ "${RPM}" ] || { echo -e "${Red}No RPM produced. ${Default}Check /tmp/${USER}_rpmbuild${OS_VER}.txt"; exit 1; } && { mkdir -p "${script_dir}/dist"; cp "${RPM}" "${script_dir}/dist"; }

DST_RPM="${script_dir}/dist/${RPM_NAME}"
read -p "sign '${DST_RPM}' now ? (y/n): " answer
case "$answer" in
  [yY])
    /usr/bin/rpm --addsign "${DST_RPM}"
    ;;
  *)
    echo "Please sign ${DST_RPM}"
    ;;
esac

/usr/bin/rm -rf /tmp/${USER}_rpmbuild
