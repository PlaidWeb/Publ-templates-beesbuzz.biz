#!/bin/sh
# Simple update script to sync in latest template changes for release purposes

SRCDIR=$HOME/Documents/beesbuzz.biz

if [ $(GIT_DIR=$SRCDIR/.git git rev-parse --abbrev-ref HEAD) != 'master' ] ; then
    echo "Error: beesbuzz.biz working directory is not on branch master"
    exit 1
fi

(
    find templates static -type f | grep -v static/_img
    echo pushl.sh
) | while read fname ; do
    if [ -f "$SRCDIR/$fname" ] && ! grep -q $fname exclusions ; then
        cp -v "$SRCDIR/$fname" "$fname"
    fi
done
