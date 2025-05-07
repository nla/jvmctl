#!/bin/bash
/usr/bin/rm -rf /tmp/rpmbuild
mkdir -p /tmp/rpmbuild
cp -r * /tmp/rpmbuild/
/usr/bin/podman run --userns=keep-id -v /tmp/rpmbuild:/home/builder/rpmbuild:Z --replace --name=rpmbuild9 localhost/rpmbuild9
script_dir=$(dirname $(readlink -f ./run_rpmbuild9_container.sh))
/usr/bin/rsync -a --delete /tmp/rpmbuild "${script_dir}/"
