#!/usr/bin/env bash

script_dir="$(dirname $0)"

source "$script_dir/.env"

function progress {
    local p=$1
    local b=$(($p*50/100))

    printf "%-*s" $((b+1)) '[' | tr ' ' '#'
    printf "%*s%3d%%\r"  $((50-b))  "]" "$p"
}


source_dir=$TS4_DECOMPRESSED_SOURCE

files=$(find $source_dir -name '*.pyc')
files_total=$(echo "$files" | wc -l)
files_done=0

for file in $files
do
    out_dir="$script_dir/ts4/$(dirname ${file#$source_dir})/"
    mkdir -p $out_dir
    rye run decompyle3 -o $out_dir $file &

    progress $(($files_done*100/$files_total))
        
    if [[ $(jobs -r | wc -l) -ge 10 ]]; then
        wait -fn
        files_done=$((files_done+1))
        progress $(($files_done*100/$files_total))
    fi
done

while [[ $(jobs -r | wc -l) -gt 0 ]]; do
    wait -fn
    files_done=$((files_done+1))
    progress $(($files_done*100/$files_total))
done

echo ""

echo "linking sims 4 modules..."

bundles=$(ls "$script_dir/ts4")

for bundle in $bundles
do
    bundle_dir="$script_dir/ts4/$bundle"
    modules=$(ls "$bundle_dir")

    for module in $modules
    do
        path="$bundle_dir/$module"
        link="$script_dir/.venv/lib/python3.7/site-packages/$module"

        echo "$path -> $link"

        rm -rf "$link"
        relative_path=$(realpath --relative-to "$(dirname $link)" "$path")
        ln -s "$relative_path" "$link"
    done
done
