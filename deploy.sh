#!/bin/sh
# deploy.sh - post-update deploy script
# see http://publ.beesbuzz.biz/441 for more information

cd "$(dirname $0)"

git pull --ff-only || exit 1

if git diff --name-only HEAD@{1} | grep -q Pipfile.lock ; then
    echo "Pipfile.lock changed; redeploying"
    pipenv install || exit 1
    # Completely restart the service, in case gunicorn updated
    systemctl --user restart beesbuzz.biz.service
elif grep -qE '^(templates/|app\.py)' ; then
    echo "Detected template or config change; restarting web services"
    # Just tell gunicorn to restart, if possible
    systemctl --user reload-or-restart beesbuzz.biz.service
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

