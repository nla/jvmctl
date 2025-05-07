#!/bin/bash
/usr/bin/podman run --userns=keep-id -v /tmp/rpmbuild:/home/builder/rpmbuild:Z --replace --name=rpmbuild8 localhost/rpmbuild8
