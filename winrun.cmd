@ECHO OFF
TITLE Publ Service
ECHO Starting up Publ...

poetry install
poetry run flask publ reindex

SET PORT=5000
SET FLASK_DEBUG=1
SET FLASK_ENV=development

poetry run flask run

