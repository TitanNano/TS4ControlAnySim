#!/usr/bin/env bash

set -euo pipefail

deploy=0
src="src"
package_name="ControlAnySim"

while [ "${1-}" != "" ]; do
    case "$1" in
        "--deploy")
            deploy=1
            ;;

        "--src")
            shift
            src="$1"
            ;;

        "--package-name")
            shift
            package_name="$1"
            ;;
    esac
    shift
done

rm -rf dist/

python3 -m compileall $src/

for file in $(find $src -name '*.pyc')
do
    file_new="${file/cpython-*.pyc/pyc}"
    file_new="${file_new/__pycache__\//}"
    file_new="${file_new/$src/dist}"

    mkdir -p $(dirname $file_new)
    mv "$file" "$file_new"
done

for cache_dir in $(find $src -name '__pycache__')
do
    rm -r $cache_dir
done

install_dir="."

if [[ $deploy -eq 1 ]]; then
    install_dir="$package_name"

    mkdir -p dist/$install_dir/
fi

cd dist/ && zip -r $install_dir/$package_name.ts4script ./control_any_sim

cd ..
cp package/*.package dist/$install_dir/

if [[ $deploy -eq 1 ]]; then
    cd dist/
    zip -r $package_name.zip ./$install_dir
fi
