@ECHO OFF
TITLE Publ Service
ECHO Starting up Publ...

SET PORT=5000
SET FLASK_DEBUG=1
SET FLASK_ENV=development
pipenv run flask run

