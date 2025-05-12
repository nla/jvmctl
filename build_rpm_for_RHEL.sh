#!/bin/bash
# WARNING: This script is designed to run the container in rootless mode (ie: as the user running the script)

Default='\e[0m';Red='\e[31m';Green='\e[32m';Yellow='\e[33m';Cyan='\e[36m';LBlue='\e[94m'

[ "${2}"  ] || { echo "$0 <name of rpm=jvmctl|sendlog|logduct> <rhel version=8|9|10>"; exit 1; }
[ -d "${1}" ] || { echo "${1} doesn't exist."; exit 2; }
case "${2}" in
  8|9|10)
    OS_VER="${2}"
    ;;
  *)
    echo "O/S version must be 8, 9 or 10";
    exit 1;
    ;;
esac

script_dir="$(dirname $(readlink -f $0))/${1}"
cd "${script_dir}"

id=$(/usr/bin/id -u)
[ "${id}" == "0" ] && { echo -e '${Red}DO NOT run as root.${Default}'; exit 1; }

name="${1}"
version=$(/usr/bin/cat VERSION)
RPM_NAME="${name}-${version}-1.el${OS_VER}.noarch.rpm"

/usr/bin/rm -rf /tmp/${USER}_rpmbuild
/usr/bin/mkdir -p /tmp/${USER}_rpmbuild
/usr/bin/rsync -a --delete * /tmp/${USER}_rpmbuild/
echo "1.el${OS_VER}" >/tmp/${USER}_rpmbuild/RELEASE

# Create the script for the container to find
cat <<SCRIPT >/tmp/${USER}_rpmbuild/rpm_build.sh
#!/bin/bash -x
# Packager: Fullname, then email
  # in the IDM world, USER is <USER>@shire.nla.gov.au
packager="\$(getent passwd "\${USER}" | awk -F: '{print \$5}') <\${USER//.nla.gov.au}@nla.gov.au>"
distro=\$(/usr/bin/awk -F: '/PLATFORM_ID/{print \$2}' /etc/os-release | sed 's:"::g')
echo distro=\$distro
mkdir -p dist
if [ -e "${name}.spec" ]
then
  arch=\$(/usr/bin/awk '/BuildArch:/{print \$2}' "${name}.spec")
  /usr/bin/sed -i -e "s~^Packager:.*~Packager: \${packager}~" -e "s~Distribution:.*~Distribution: \${distro}~" ${name}.spec 
  /usr/bin/rpmbuild -bb ${name}.spec
  pwd
  /usr/bin/ls -l "/tmp/rpmbuild/RPMS/\${arch}/"
  /usr/bin/mv -v /tmp/rpmbuild/RPMS/\${arch}/*.rpm dist/
   # 2>/dev/null
else
  /usr/bin/python3 setup.py clean bdist_rpm --release 0.\${distro} --vendor NLA --packager "\${packager}" --distribution-name "\${distro}"
fi
SCRIPT

/usr/bin/podman run --userns=keep-id -h $HOSTNAME -v /tmp/${USER}_rpmbuild:/tmp/rpmbuild:Z --replace --name=rpmbuild${OS_VER} localhost/rpmbuild${OS_VER} >/tmp/${USER}_rpmbuild${OS_VER}.txt 2>&1

RPM=$(/usr/bin/ls /tmp/${USER}_rpmbuild/dist/${RPM_NAME} 2>/dev/null)
[ "${RPM}" ] || { echo -e "${Red}No RPM produced. ${Default}Check /tmp/${USER}_rpmbuild${OS_VER}.txt"; exit 1; } && { mkdir -p "${script_dir}/dist"; cp "${RPM}" "${script_dir}/dist/"; }

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
