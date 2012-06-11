#!/bin/bash
set -e

# get source of current branch
rm -rf src/
git clone "../../" src
rm -rf src/.git/
rm -rf src/.gitignore

rm -rf tree/
mkdir -p tree/opt/
cp -r DEBIAN tree

dpkg --build tree ./ 

rm -rf src/

exit 0