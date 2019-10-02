#!/bin/sh
# Posts a quick IndieWeb-style response to the blog/chatter category
# For example:
#
# ./pub.sh like-of http://example.com/a-good-post
# ./pub.sh rsvp http://example.com/party yes
# ./pub.sh in-reply-to http://example.com/blahblahblah
#
# Prints out the filename so the body can be further edited

type=$1; shift
url=$1; shift

basename="$(date +%Y%m%d)-$type-$(echo -n $url | tr -c [a-zA-Z0-9_-] _ | sed s/_+/_/g)"
fname="$(dirname "$0")/content/blog/chatter/$basename.md"
echo $fname

cat > $fname << EOF
Title: $type
$type: $url $*


EOF
