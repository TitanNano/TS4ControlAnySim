#!/usr/bin/env bash

set -euo pipefail

deploy=0
src="src"
package_name="ControlAnySim"
test=0

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

        "--test")
            test=1
            ;;
    esac
    shift
done

if [[ -f ".env" ]]; then
    source .env
fi

rm -rf dist/

current_version=$(git describe --tag)
echo "__version__ = \"${current_version:1}\"" > src/control_any_sim/__init__.py

uv run python3 -m compileall $src/

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
cp LICENSE dist/$install_dir/LICENSE.txt

if [[ $deploy -eq 1 ]]; then
    cd dist/
    zip -r $package_name.zip ./$install_dir
    cd ..
fi

git checkout src/control_any_sim/__init__.py

if [[ $test -eq 1 ]]; then
    cp -r dist/$install_dir/*.{package,ts4script} "$TS4_MODS_DIR/$package_name/"

    "$TS4_BIN"
fi
