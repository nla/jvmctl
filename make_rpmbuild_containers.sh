#!/bin/bash
cd ""$(dirname $0)"" || exit 2
Default='\e[0m';Red='\e[31m';Green='\e[32m';Yellow='\e[33m';Cyan='\e[36m';LBlue='\e[94m'

[ "${1}"  ] || { echo "$0 <rhel version=8|9|10>"; exit 1; }
[ -d "build_rhel${1}_container" ] || { echo -e "${Red}The directory 'build_rhel${1}_container' doesn't exist.${Default}"; exit 2; }

case "${1}" in
  8|9|10)
    if ! curl -sq --connect-timeout 3 https://google.com >/dev/null
    then
      [ -e "$(pwd)/proxy.sh" ] && source "$(pwd)/proxy.sh" || { echo -e "${Red}Unable to access internet, please setup '$(pwd)/proxy.sh'.${Default}"; exit 10; }
    fi

    cd "build_rhel${1}_container/" || exit 3
    /usr/bin/podman build -f Dockerfile -t rpmbuild${1}
    /usr/bin/podman image prune -f
    /usr/bin/podman images | /usr/bin/grep rpmbuild${1} | /usr/bin/head -n1
    ;;
  *)
    echo -e "${Red}O/S version must be 8, 9 or 10.${Default}";
    exit 2;
    ;;
esac
