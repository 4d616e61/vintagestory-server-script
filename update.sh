

set -e


#TODO: find url based on version, auto grab latest
#Usage: update.sh https://cdn.vintagestory.at/gamefiles/stable/vs_server_linux-x64_1.20.9.tar.gz


cd "$(dirname "$0")"
rm -rf vintagestory
mkdir vintagestory





curl $1 | tar -xvz -C vintagestory
