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

        # Twitter API keys are configured in the environment via systemd unit
        'TWITTER_CLIENT_KEY': os.environ.get('TWITTER_CLIENT_KEY'),
        'TWITTER_CLIENT_SECRET': os.environ.get('TWITTER_CLIENT_SECRET'),

        # if I'm running locally I want access to the `test:` pseudo-users
        'TEST_ENABLED': os.environ.get('FLASK_DEBUG'),
    },

    # Keep 3 months of authentication logs
    'auth_log_prune_age': 86400 * 90,
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


def thread_id(item):
    """ Compute an Isso thread URI for the entry.

    This allows me to use Isso for comments on private entries without
    having to worry about people guessing the secret thread ID; If they can
    see the thread ID it's because they have access to the entry already.
    """
    if not isinstance(item, publ.entry.Entry):
        raise ValueError("got non-entry object %s" % type(item))

    key = str(item.id)
    tid = hmac.new(b'SECRET KEY HERE',
                   key.encode('utf-8'), 'md5').hexdigest()[:16]

    return f'/{tid}/{key}'


# register the thread ID generator with the templating system
app.jinja_env.globals.update(thread_id=thread_id)

@app.template_filter('hashtag')
def make_hashtag(words : str):
    """ Adds a custom Jinja filter to turn a sentence into a #HashTag. Used
    in feed-twitter.xml """
    words = words.replace("'", '')
    words = re.split(r'[^a-zA-Z0-9]+', words)

    return ''.join([w.title() if w.islower() else w for w in words])

@app.route('/favicon.ico')
def favicon():
    """
    Add a route for serving up an old-style favicon. This could also be
    implemented using flask.send_file() and a file stored outside of the content
    directory.

    If you want to get really fancy you could do:

        return flask.redirect(
            publ.image.get_image('favicon.png', ())
                .get_rendition(format='ico',width=32,height=32)[0])

    which will dynamically render the file 'favicon.png' in the content
    directory root into a 32x32 .ico file, although this is extreme overkill.
    """
    return flask.redirect(flask.url_for('static', filename='favicon.ico'))


@app.path_alias_regex(r'/(d|comics)/(.*/)?(?P<date>[0-9]{6,8}(_w)?)\.php')
def redirect_comics(match):
    """
    This is an example of how to migrate old URLs to new ones; my old site
    had date-based views like:

        http://beesbuzz.biz/d/201006.php

    which this now turns into:

        http://beesbuzz.biz/comics/?date=201006

    This also handles the occasional case of a legacy news post that did a
    relative link to the old URL.
    """
    return flask.url_for('category', category='comics', date=match.group('date')), True


@app.path_alias_regex(r'/blog/e/')
@app.path_alias_regex(r'/forum/')
def redirect_blog_content(match):
    """
    Another URL migration example; this redirects legacy blog and forum content
    to the latest archive.org snapshot if another page hasn't already claimed
    the legacy path.
    """
    return 'https://web.archive.org/web/*/' + flask.request.url, False


@app.path_alias_regex(r'/([^/]+)/.*rss.php')
def redirect_subfeed(match):
    """
    URL migration: my site used to have per-category/subcategory RSS feeds
    as /category/path/rss.php. Many of the categories have Path-Aliases
    in their respective .cat files, but some of the old subcategories no
    longer apply, so now I just bulk-redirect all unaccounted-for subcategories
    to the top-level category's feed.
    """
    return flask.url_for(
        'category',
        category=match.group(1),
        template='feed'), True


@app.after_request
def add_webmention_endpoint(response):
    """
    This publishes a webmention endpoint for everything, including error pages
    (necessary for receiving pings to private entries) and image resources.
    Please fix the endpoint URL before uncommenting this.
    """
    #response.headers.add('link', '<https://webmention.io/DOMAIN_GOES_HERE/webmention>; rel="webmention"')
    return response


@app.path_alias_regex(r'/\.well-known/(host-meta|webfinger).*')
def redirect_bridgy(match):
    """
    This redirects ActivityPub activity to fed.brid.gy. See
    https://fed.brid.gy/#use for usage. You can follow my site
    at @beesbuzz.biz@beesbuzz.biz on Mastodon et al if you want.
    """
    return 'https://fed.brid.gy' + flask.request.full_path, False
