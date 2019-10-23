#!/usr/bin/env bash

src="src"

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

cd dist && zip -r ControlAnySim.ts4script ./

cd ..
cp package/*.package dist/
