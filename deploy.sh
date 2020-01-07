#!/bin/sh
# wrapper script to pull the latest site content and redeploy

cd "$(dirname $0)"

# see where in the history we are now
PREV=$(git rev-parse --short HEAD)

git pull --ff-only || exit 1

if git diff --name-only $PREV | grep -qE '^(templates/|app\.py)' ; then
    echo "Configuration or template change detected"
    disposition=reload-or-restart
fi

if git diff --name-only $PREV | grep -q Pipfile.lock ; then
    echo "Pipfile.lock changed"
    pipenv install || exit 1
    disposition=restart
fi

if [ "$1" != "nokill" ] && [ ! -z "$disposition" ] ; then
    systemctl --user $disposition beesbuzz.biz.service
fi

# Wait for the socket to exist before trying to run push
count=0
while [ $count -lt 5 ] && [ ! -S $HOME/.vhosts/beesbuzz.biz ] ; do
    count=$(($count + 1))
    echo "Waiting for service to restart... ($count)"
    sleep $count
done

echo "Sending push notifications"
nohup ./pushl.sh

