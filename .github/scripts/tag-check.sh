#!/bin/bash
regex="^(registry\.cn-hangzhou\.aliyuncs\.com\/|coseus\.azurecr\.io\/)[a-zA-Z0-9_\./\-]+:[a-zA-Z0-9_\./\-]+$"

yq '[.. | select(has("image"))] | .[].image' $1 | sed -E -n "/$regex/p" | sort | uniq |
  while read line; do
    skopeo inspect --override-arch amd64 --override-os linux docker://$line >/dev/null 2>&1
    if [ $? -ne 0 ]; then
      echo "$line does not exist"
      # break
    else
      echo "$line exists"
    fi
  done
