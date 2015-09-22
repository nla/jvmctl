#!/bin/bash

if [ -z "$1"]; then
    echo 'Usage: $0 version-number'
    exit 1
fi

VERSION="$1"
sed -i "s/^VERSION = /VERSION = '$VERSION'/" jvmctl
echo $VERSION > VERSION
git add jvmctl VERSION
git commit -m"Release $VERSION"
git tag "$VERSION"
git push origin master "$VERSION"
rake build
