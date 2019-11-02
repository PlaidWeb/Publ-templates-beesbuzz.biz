#!/bin/sh
# deploy.sh - post-update deploy script
# see http://publ.beesbuzz.biz/441 for more information

cd "$(dirname $0)"

git pull --ff-only || exit 1

if git diff --name-only HEAD@{1} | grep -q Pipfile.lock ; then
    echo "Pipfile.lock changed; redeploying"
    pipenv install || exit 1
fi

if [ "$1" != "nokill" ]; then
    echo "Restarting web services"
    killall -HUP gunicorn
fi

echo "Sending push notifications"
nohup ./pushl.sh
