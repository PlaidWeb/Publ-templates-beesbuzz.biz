""" Main Publ application """

import os
import logging
import logging.handlers
import hmac

import publ
import flask
import authl.flask

logging.basicConfig(level=logging.INFO)

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
        'CACHE_DEFAULT_TIMEOUT': 3613,
        'CACHE_KEY_PREFIX': 'beesbuzz.biz',
    } if not os.environ.get('FLASK_DEBUG') else {
        'CACHE_NO_NULL_WARNING': True
    },

    # This is probably not necessary but it makes me feel better.
    'index_rescan_interval': 86400,

    # set up private posts
    'auth': {
        # Always use SSL in production
        'AUTH_FORCE_HTTPS': not os.environ.get('FLASK_DEBUG'),

        # I have an SMTP server running on localhost
        'SMTP_HOST': 'localhost',
        'SMTP_PORT': 25,
        'EMAIL_FROM': 'nobody@beesbuzz.biz',
        'EMAIL_SUBJECT': 'Sign in to beesbuzz.biz',

        # Identify my site as "busybee" to the Mastodon login flow
        'FEDIVERSE_NAME': 'busybee',
        'FEDIVERSE_HOMEPAGE': 'http://beesbuzz.biz/',

        # enable IndieAuth support using the default client_id shim
        'INDIEAUTH_CLIENT_ID': authl.flask.client_id,

        # if I'm running locally I want access to the `test:` pseudo-users
        'TEST_ENABLED': os.environ.get('FLASK_DEBUG'),
    },
}

app = publ.Publ(__name__, config)

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

