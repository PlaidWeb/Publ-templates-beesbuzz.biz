#!/bin/sh
# Simple update script to sync in latest template changes for release purposes

SRCDIR=$HOME/Documents/beesbuzz.biz
find templates static -type f | grep -v static/_img | while read fname ; do
    if [ -f "$SRCDIR/$fname" ] && ! grep -q $fname exclusions ; then
        cp -v "$SRCDIR/$fname" "$fname"
    fi
done
