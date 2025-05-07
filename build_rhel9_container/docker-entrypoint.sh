#!/bin/bash -x
# check for rpm_build.sh and run it.
cd /home/builder/rpmbuild/
dir=$(pwd)
for script in $(ls rpm_build.sh */rpm_build.sh 2>/dev/null);
do 
  echo "Runinng script: ${script} ..."
  cd "${dir}/$(dirname "${script}")"
  bash -x ./rpm_build.sh
done
