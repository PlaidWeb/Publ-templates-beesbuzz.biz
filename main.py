""" Main Publ application """


import os
import logging
import logging.handlers

import publ
from dateutil import tz


if os.path.isfile('logging.conf'):
    logging.config.fileConfig('logging.conf')
else:
    if not os.path.isdir('logs'):
        os.makedirs('logs')
    logging.basicConfig(level=logging.INFO,
                        handlers=[
                            logging.handlers.TimedRotatingFileHandler(
                                'logs/publ.log'),
                            logging.StreamHandler()
                        ],
                        format="%(levelname)s:%(threadName)s:%(name)s:%(message)s")

logging.info("Setting up")

APP_PATH = os.path.dirname(os.path.abspath(__file__))

config = {
    'database_config': {
        'provider': 'sqlite',
        'filename': os.path.join(APP_PATH, 'index.db')
    },
    'timezone': 'US/Pacific',
    'cache': {
        'CACHE_TYPE': 'simple',
        'CACHE_DEFAULT_TIMEOUT': 60,
        'CACHE_THRESHOLD': 500
    } if not os.environ.get('FLASK_DEBUG') else {},
    'index_rescan_interval': 86400
}

app = publ.publ(__name__, config)

import flask


@app.route('/favicon.ico')
def favicon():
    """ Add a route for serving up the favicon """
    return flask.redirect(flask.url_for('static', filename='favicon.ico'))


@app.path_alias_regex(r'/d/([0-9]{8}(_w)?)\.php')
def redirect_date(match):
    """ This is an example of how to migrate old URLs to new ones; my old site
    had date-based views like:

    http://beesbuzz.biz/d/201006.php

    which this now turns into:

    http://beesbuzz.biz/comics/?date=201006 """
    return flask.url_for('category', category='comics', date=match.group(1)), True


@app.path_alias_regex(r'/blog/e/')
def redirect_blog_entry(match):
    ''' Another URL migration example; this redirects legacy blog content
    to the 'missing content' entry if another page hasn't already claimed the
    legacy path. '''
    return flask.url_for('entry', entry_id=7821), False


@app.path_alias_regex(r'/\.well-known/(host-meta|webfinger).*')
def redirect_bridgy(match):
    ''' This redirects ActivityPub activity to fed.brid.gy. See
    https://fed.brid.gy/#use for usage. '''
    return 'https://fed.brid.gy' + flask.request.full_path, False

if __name__ == "__main__":
    app.run(port=os.environ.get('PORT', 5000))
