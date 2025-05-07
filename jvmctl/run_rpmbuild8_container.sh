#!/bin/bash
# WARNING: This script is designed to run the container in rootless mode (ie: as the user running the script)

VER=8
Default='\e[0m';Red='\e[31m';Green='\e[32m';Yellow='\e[33m';Cyan='\e[36m';LBlue='\e[94m'
script_dir=$(dirname $(readlink -f $0))
cd "${script_dir}"

id=$(/usr/bin/id -u)
[ "${id}" == "0" ] && { echo -e '$RedDO NOT runn as root'; exit 1; }


/usr/bin/rm -rf /tmp/${USER}_rpmbuild
mkdir -p /tmp/${USER}_rpmbuild
cp -r * /tmp/${USER}_rpmbuild/
/usr/bin/podman run --userns=keep-id -v /tmp/${USER}_rpmbuild:/tmp/rpmbuild:Z --replace --name=rpmbuild${VER} localhost/rpmbuild${VER} >/tmp/${USER}_rpmbuild${VER}.txt 2>&1
SRC_RPM=$(ls /tmp/${USER}_rpmbuild/dist.el${VER}/*noarch.rpm 2>/dev/null)
[ "${SRC_RPM}" ] || { echo -e "${Red}No RPM produced. ${Default}Check /tmp/${USER}_rpmbuild${VER}.txt"; exit 1; } && { mkdir -p "${script_dir}/dist"; cp "${SRC_RPM}" "${script_dir}/dist"; }
RPM="$(ls ${script_dir}/dist | grep -v '\.el')"
DST_RPM="$(echo ${RPM} | sed "s:.noarch:.el${VER}.noarch:")"
mv "dist/${RPM}" "dist/${DST_RPM}"

read -p "sign 'dist/${DST_RPM}' now ? (y/n): " answer
case "$answer" in
  [yY])
    rpm --addsign "dist/${DST_RPM}"
    break
    ;;
  *)
    echo "Please sign dist/${DST_RPM}"
    ;;
esac

