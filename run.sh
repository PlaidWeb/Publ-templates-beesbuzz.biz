#!/bin/sh

poetry install
poetry run flask publ reindex
FLASK_DEBUG=1 FLASK_ENV=development poetry run flask run
