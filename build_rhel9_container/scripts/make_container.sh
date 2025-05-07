#!/bin/bash
if ! curl -sq --connect-timeout 3 https://google.com >/dev/null
then
  export http_proxy="http://admin.nla.gov.au:3128"
  export https_proxy="http://admin.nla.gov.au:3128"
  export no_proxy="127.0.0.1, localhost, nla.gov.au"
  export HTTP_PROXY="${http_proxy}"
  export HTTPS_PROXY="${https_proxy}"
  export NO_PROXY="${no_proxy}"
fi

cd $(dirname $0)/..
/usr/bin/podman build -f Dockerfile -t rpmbuild9
/usr/bin/podman images | /usr/bin/grep rpmbuild9 | /usr/bin/head -n1 
