#!/bin/bash
VER=8
Default='\e[0m';Red='\e[31m';Green='\e[32m';Yellow='\e[33m';Cyan='\e[36m';LBlue='\e[94m'
script_dir=$(dirname $(readlink -f $0))
cd "${script_dir}"

/usr/bin/rm -rf /tmp/rpmbuild
mkdir -p /tmp/rpmbuild
cp -r * /tmp/rpmbuild/
/usr/bin/podman run --userns=keep-id -v /tmp/rpmbuild:/home/builder/rpmbuild:Z --replace --name=rpmbuild${VER} localhost/rpmbuild${VER} >/tmp/rpmbuild${VER}.txt 2>&1
SRC_RPM=$(ls /tmp/rpmbuild/dist.el${VER}/*noarch.rpm 2>/dev/null)
[ "${SRC_RPM}" ] || { echo -e "${Red}No RPM produced. ${Default}Check /tmp/rpmbuild${VER}.txt"; exit 1; } && { mkdir -p "${script_dir}/dist"; cp "${SRC_RPM}" "${script_dir}/dist"; }
RPM="$(ls ${script_dir}/dist | grep -v '\.el')"
DST_RPM="$(echo ${RPM} | sed "s:.noarch:.el${VER}.noarch:")"
mv "dist/${RPM}" "dist/${DST_RPM}"
echo "Please sign dist/$(ls ${script_dir}/dist)"
