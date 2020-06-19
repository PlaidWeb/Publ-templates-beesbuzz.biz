#!/bin/sh

pipenv run flask publ reindex
FLASK_DEBUG=1 FLASK_ENV=development pipenv run flask run
