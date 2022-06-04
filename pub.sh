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

basename="$(date +%Y%m%d) $type_$(printf '%s' "$url" | tr -cs '[a-zA-Z0-9_\-\n]' _ | sed 's/_+/_/g;s/_$//g')"
fname="$(dirname "$0")/content/blog/chatter/$basename.md"
printf "'%s'" "$fname"

cat > $fname << EOF
Status: DRAFT
Title:
$type: $url $*


EOF
