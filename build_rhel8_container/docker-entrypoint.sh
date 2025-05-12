#!/bin/bash -x
# check for rpm_build.sh and run it.
owner=$(stat -c '%U' /tmp/rpmbuild)
cd /tmp/rpmbuild/
dir=$(pwd)
for script in $(ls rpm_build.sh */rpm_build.sh 2>/dev/null);
do 
  echo "Running script: ${script} ..."
  cd "${dir}/$(dirname "${script}")"
  chmod +x rpm_build.sh
  # preserve file ownership so the user who ran this can cleanup the files
  runuser -u $owner ./rpm_build.sh
done
