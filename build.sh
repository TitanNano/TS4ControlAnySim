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

compile_source() {
    uv run python3 -m compileall "$src/"

    for file in $(find $src -name '*.pyc')
    do
        file_new="${file/cpython-*.pyc/pyc}"
        file_new="${file_new/__pycache__\//}"
        file_new="${file_new/$src/dist}"

        mkdir -p "$(dirname "$file_new")"
        mv "$file" "$file_new"
    done

    for cache_dir in $(find $src -name '__pycache__')
    do
        rm -r "$cache_dir"
    done

    cd dist/ && zip -r "$install_dir/$package_name".ts4script ./control_any_sim
    cd ..
}

build_package() {
    if ! [[ -d .s4-tools/ ]]; then
        git clone https://github.com/simsonianlibrary/s4-shell-tools .s4-tools
    fi

    cd .s4-tools/
    git reset --hard
    git checkout 1ff833eb1e4fdd5af59e6886881738c493bf1082
    npm i
    npx tsc
    mkdir -p out
    cp -r dist/** out/
    cd ..

    node .s4-tools/out/S4ShellTools.js build --config package/build.yaml
}

install_dir="."

if [[ $deploy -eq 1 ]]; then
    install_dir="$package_name"

    mkdir -p "dist/$install_dir/"
fi

compile_source
build_package

cp package/build/ControlAnySim.package "dist/$install_dir/"
cp LICENSE "dist/$install_dir/LICENSE.txt"

if [[ $deploy -eq 1 ]]; then
    cd dist/
    zip -r "$package_name.zip" "./$install_dir"
    cd ..
fi

git checkout src/control_any_sim/__init__.py

if [[ $test -eq 1 ]]; then
    cp -r dist/"$install_dir"/*.{package,ts4script} "$TS4_MODS_DIR/$package_name/"

    "$TS4_BIN"
fi
