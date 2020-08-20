#!/bin/sh

# first argument is container name
# second is object
# third, choose swift or curl

[ -z "${OS_AUTH_TOKEN}" -o -z "${OS_STORAGE_URL}" ] && echo "missing auth variables" && exit 1

echo "$1"
echo "$(dirname $2)"

if [ $3 = "swift" ]
then
  # with SWIFT, support folder
  swift --insecure --debug \
   --os-storage-url "${OS_STORAGE_URL}" --os-auth-token "${OS_AUTH_TOKEN}" \
   download $1 -p $2

elif [ $3 = "curl" ]
then
  # with CURL, only file
  mkdir -p $(dirname $2)
  curl -i -k \
      "${OS_STORAGE_URL}/$1/$2" \
      -X GET \
      -H "X-Auth-Token: ${OS_AUTH_TOKEN}" \
      -o $2

else
  echo "Choose swift or curl"
  exit 1
fi
