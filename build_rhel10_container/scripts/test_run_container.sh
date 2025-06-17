#!/bin/bash
/usr/bin/podman run --userns=keep-id -v /tmp/rpmbuild:/home/builder/rpmbuild:Z --replace --name=rpmbuild10 localhost/rpmbuild10
