""" Main Publ application """

import os
import logging
import logging.handlers

import publ
import flask

# This logging configuration is way overcomplicated and is mostly for my own
# debugging of Publ itself. You don't really have to do this.
if os.path.isfile('logging.conf'):
    logging.config.fileConfig('logging.conf')
else:
    try:
        os.makedirs('logs')
    except FileExistsError:
        pass
    logging.basicConfig(level=logging.INFO,
                        handlers=[
                            logging.handlers.TimedRotatingFileHandler(
                                'logs/publ.log', when='D'),
                            logging.StreamHandler()
                        ],
                        format="%(levelname)s:%(threadName)s:%(name)s:%(message)s")

logging.info("Setting up")

APP_PATH = os.path.dirname(os.path.abspath(__file__))

config = {
    # use SQLite with the persistent index stored locally	
    'database_config': {
        'provider': 'sqlite',
        'filename': os.path.join(APP_PATH, 'index.db')
    },

    # West coast is best coast
    'timezone': 'US/Pacific',

    # I don't expect my content to change more often than every 5 minutes.
    # I'm running on my own server with plenty of RAM.
    'cache': {
        'CACHE_TYPE': 'simple',
        'CACHE_DEFAULT_TIMEOUT': 300,
        'CACHE_THRESHOLD': 500
    } if not os.environ.get('FLASK_DEBUG') else {},

    # This is probably not necessary but it makes me feel better.
    'index_rescan_interval': 86400
}

app = publ.publ(__name__, config)


@app.route('/favicon.ico')
def favicon():
    """ Add a route for serving up the favicon. This could also be implemented using flask.send_file(). """
    return flask.redirect(flask.url_for('static', filename='favicon.ico'))


@app.path_alias_regex(r'/d/([0-9]{8}(_w)?)\.php')
def redirect_date(match):
    """
    This is an example of how to migrate old URLs to new ones; my old site
    had date-based views like:

    http://beesbuzz.biz/d/201006.php

    which this now turns into:

    http://beesbuzz.biz/comics/?date=201006
    """
    return flask.url_for('category', category='comics', date=match.group(1)), True


@app.path_alias_regex(r'/blog/e/')
def redirect_blog_entry(match):
    """
    Another URL migration example; this redirects legacy blog content
    to the 'missing content' entry if another page hasn't already claimed the
    legacy path.
    """
    return flask.url_for('entry', entry_id=7821), False


@app.path_alias_regex(r'/\.well-known/(host-meta|webfinger).*')
def redirect_bridgy(match):
    """
    This redirects ActivityPub activity to fed.brid.gy. See
    https://fed.brid.gy/#use for usage. You can follow my site
    at @beesbuzz.biz@beesbuzz.biz on Mastodon et al if you want.
    """
    return 'https://fed.brid.gy' + flask.request.full_path, False


if os.environ.get('FLASK_PROFILE'):
    """ Useful for basic performance testing, although this doesn't really tell me much. """
    import flask_profiler
    app.config['flask_profiler'] = {
        'enabled': True,
        'storage': {
            'engine': 'sqlite',
        },
        'ignore': [
            '^/static/.*'
        ]
    }
    flask_profiler.init_app(app)


if __name__ == "__main__":
    """
    Only used for local testing. My real server runs it via systemd. See
    http://publ.beesbuzz.biz/manual/deploying/1278-Apache-mod-proxy-or-nginx
    for details.
    """
    app.run(port=os.environ.get('PORT', 5000))

