""" Main Publ application """

import os
import logging
import logging.handlers

import publ
import flask
import authl.flask

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
    # I use SQLite with the persistent index stored locally.
    'database_config': {
        'provider': 'sqlite',
        'filename': os.path.join(APP_PATH, 'index.db')
    },

    # West coast is best coast
    'timezone': 'US/Pacific',

    # I don't expect my content to change more often than every 5 minutes.
    # I'm running on a server with a local memcached instance.
    'cache': {
        'CACHE_TYPE': 'memcached',
        'CACHE_DEFAULT_TIMEOUT': 300,
        'CACHE_KEY_PREFIX': 'beesbuzz.biz',
    } if not os.environ.get('FLASK_DEBUG') else {},

    # This is probably not necessary but it makes me feel better.
    'index_rescan_interval': 86400,

    # set up private posts
    'auth': {
        # Always use SSL in production
        'AUTH_FORCE_SSL': not os.environ.get('FLASK_DEBUG'),

        # I have an SMTP server running on localhost
        'SMTP_HOST': 'localhost',
        'SMTP_PORT': 25,
        'EMAIL_FROM': 'nobody@beesbuzz.biz',
        'EMAIL_SUBJECT': 'Sign in to beesbuzz.biz',

        # Identify my site as "busybee" to the Mastodon login flow
        'MASTODON_NAME': 'busybee',
        'MASTODON_HOMEPAGE': 'http://beesbuzz.biz/',

        # enable IndieAuth support using the default client_id shim
        'INDIEAUTH_CLIENT_ID': authl.flask.client_id,

        # IndieLogin.com support is waiting on https://github.com/aaronpk/indielogin.com/issues/38
        # 'INDIELOGIN_CLIENT_ID': 'https://beesbuzz.biz/',

        # if I'm running locally I want access to the `test:` pseudo-users
        'TEST_ENABLED': os.environ.get('FLASK_DEBUG'),
    },
}

app = publ.publ(__name__, config)

# Create a persistent secret session key that's never checked in
if not os.path.isfile('.sessionkey'):
    import uuid
    with open('.sessionkey', 'w') as file:
        file.write(str(uuid.uuid4()))
    os.chmod('.sessionkey', 0o600)
with open('.sessionkey') as file:
    app.secret_key = file.read()


# provide a thread ID generator for the comment threads
def thread_id(item):
    """ Compute an Isso thread URI for the entry """
    if not isinstance(item, publ.entry.Entry):
        raise ValueError("got non-entry object %s" % type(item))

    key = str(item.id)
    tid = hmac.new(b'SECRET KEY HERE',
                   key.encode('utf-8')).hexdigest()[:16]

    return f'/{tid}/{key}'

# register the thread ID generator with the templating system
app.jinja_env.globals.update(thread_id=thread_id)


@app.route('/favicon.ico')
def favicon():
    """ Add a route for serving up the favicon. This could also be implemented
    using flask.send_file() and a file stored outside of the content directory. """
    return flask.redirect(flask.url_for('static', filename='favicon.ico'))


@app.path_alias_regex(r'/d/([0-9]{6,8}(_w)?)\.php')
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
