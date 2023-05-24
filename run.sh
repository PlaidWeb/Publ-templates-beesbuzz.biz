#!/bin/sh
set -e
cd "$(dirname $0)"
poetry install
poetry run flask publ reindex
FLASK_DEBUG=1 poetry run flask run "$@"

