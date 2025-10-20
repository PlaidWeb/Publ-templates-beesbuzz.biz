""" Main Publ application """

import os
import logging
import logging.handlers
import hmac

import publ
import flask
import authl.flask
import user_agents

logging.basicConfig(level=logging.INFO)

logging.info("Setting up")

APP_PATH = os.path.dirname(os.path.abspath(__file__))

if 'DATABASE_URL' in os.environ:
    # This makes it easier to use mysql in production, with an environment
    # variable like
    # DATABASE_URL=mysql://username:password@server/dbname
    import urllib.parse
    parsed = urllib.parse.urlparse(os.environ['DATABASE_URL'])
    user = re.match(r'(.*):(.*)@(.*)', parsed.netloc)
    db_config = {
        'provider': parsed.scheme,
        'user': user.group(1),
        'password': user.group(2),
        'host': user.group(3),
        'database': parsed.path[1:],
        'charset': 'utf8mb4',
        'collation': 'utf8mb4_bin',
    }
else:
    # Without DATABASE_URL I use a local sqlite (in staging etc.)
    db_config = {'provider': 'sqlite',
                 'filename': os.path.join(APP_PATH, 'index.db')}


config = {
    'database_config': db_config,

    # West coast is best coast
    'timezone': 'US/Pacific',

    # I'm running on a server with a local memcached instance.
    # Publ automatically invalidates the cache for content changes,
    # so the cache timeout mostly is just there so that humanized
    # dates (e.g. "1 hour ago") update relatively often.
    'cache': {
        'CACHE_TYPE': 'memcached',
        'CACHE_DEFAULT_TIMEOUT': 3613,
        'CACHE_KEY_PREFIX': 'beesbuzz.biz',
    } if not os.environ.get('FLASK_DEBUG') else {
        'CACHE_NO_NULL_WARNING': True
    },

    # This is probably not necessary but it makes me feel better.
    'index_rescan_interval': 86400,

    # If running in production, don't enable the watchdog; this allows me to more
    # easily work on entries "live"
    'index_enable_watchdog': bool(os.environ.get('FLASK_DEBUG')),

    # set up private posts
    'auth': {
        # Always use SSL in production
        'AUTH_FORCE_HTTPS': not os.environ.get('FLASK_DEBUG'),

        # I have an SMTP server running on localhost
        'SMTP_HOST': 'localhost',
        'SMTP_PORT': 25,
        'EMAIL_FROM': 'nobody@example.com',
        'EMAIL_SUBJECT': 'Sign in to beesbuzz.biz',

        # Identify my site as "busybee" to the Mastodon login flow
        'FEDIVERSE_NAME': 'busybee',
        'FEDIVERSE_HOMEPAGE': 'http://beesbuzz.biz/',

        # enable IndieAuth support using the default client_id shim
        'INDIEAUTH_CLIENT_ID': authl.flask.client_id,

        # if I'm running locally I want access to the `test:` pseudo-users
        'TEST_ENABLED': os.environ.get('FLASK_DEBUG'),
    },

    # Keep 3 months of authentication logs
    'auth_log_prune_age': 86400 * 90,

    # Provides some default layout rules (particularly image renditions)
    'layout': {
        'max_width': 960,
        'max_height': 960,
        'fullsize_width': 3840,
        'fullsize_height': 2160,
        'fullsize_quality': 35,
        'resize': 'fit',
        'figure': 'images',
        'heading_link_class': 'toc_link',
        'img_class': 'u-photo',
        'format': 'webp',
        'quality': 35
    },

    'search_index': 'search'
}

# Create a persistent secret session key that's never checked in.
# If this site were running behind a load balancer this file would need to
# be shared amongst all of the backing instances.
if not os.path.isfile('.sessionkey'):
    import uuid
    with open('.sessionkey', 'w') as file:
        file.write(str(uuid.uuid4()))
    os.chmod('.sessionkey', 0o600)
with open('.sessionkey') as file:
    config['secret_key'] = file.read()

app = publ.Publ(__name__, config)


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
def make_hashtag(words: str):
    """
    A filter to convert a bunch of words into a hashtag like #ABunchOfWords
    """
    words = words.replace("'", '')
    words = re.split(r'[^a-zA-Z0-9]+', words)

    return ''.join([w.title() if w.islower() else w for w in words])


@app.template_filter('shuffle')
def filter_shuffle(seq):
    """
    A custom sort filter to shuffle the order of items
    """
    try:
        result = list(seq)
        random.shuffle(result)
        return result
    except:
        return seq


@app.template_filter('sort_latest')
def filter_sort_latest(seq, **kwargs):
    """
    A custom sort filter to sort categories by their latest update,
    used by the _mainpage template
    """
    try:
        result = list(seq)

        def get_latest_date(cc):
            ee = cc.last(**kwargs)
            return ee.date if ee else arrow.get()
        result.sort(key=get_latest_date, reverse=True)
        return result
    except:
        logging.exception("Couldn't sort list %s", seq)
        return seq


@app.template_filter('entry_urls')
def filter_get_entry_urls(entry):
    """
    This lets me track multiple entry URLs for webmention.js, by adding
    Old-Url: headers
    """

    from urllib.parse import urlparse, urlunparse

    urls = {entry.link(), entry.link(expand=False, absolute=True)
            } | set(entry.get_all('old-url'))

    urls = {urlunparse(urlparse(url)._replace(
        netloc='beesbuzz.biz', scheme='https')) for url in urls}

    urls -= {flask.request.url}

    return urls


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


@app.route('/error/<int:code>')
def raise_error(code):
    """
    This lets people poke at my various error code handlers by going to
    /error/404, /error/403, etc.
    """
    werkzeug.exceptions.abort(code)


@app.route('/_indexing')
def index_length():
    """
    This is a useful helper function so that my deployment scripts can
    wait until indexing completes before sending update notifications
    with Pushl
    """
    import publ.index
    return f'{publ.index.queue_size()}'


@app.path_alias_regex(r'/([^/]+)/.*rss.php')
def redirect_subfeed(match):
    """
    URL migration: my site used to have per-category/subcategory RSS feeds
    as /category/path/rss.php. Many of the categories have Path-Aliases
    in their respective .cat files, but some of the old subcategories no
    longer apply, so now I just bulk-redirect all unaccounted-for subcategories
    to the top-level category's feed.

    There are, surprisingly, still people accessing these old feed URLs, a
    decade later.
    """
    return flask.url_for(
        'category',
        category=match.group(1),
        template='feed'), True


@app.before_request
def antiscraper():
    """
    This request-hook will use the user_agents package to detect whether there's
    a bot accessing the site, and if so, adds an 'is_bot' attribute to the global
    store, which is then available to the page templates to remove elements that
    cause issues with web scrapers (such as tag lists, which can lead to a
    combinatoric explosion of useless page requests).

    If something is performing access patterns which are likely bot activity,
    it sends them to the login page as a form of sentience test and generally
    discouraging bad scraper behavior.
    """
    # Flag bots to remove page elements
    if user_agents.parse(flask.request.headers.get('User-Agent', '')).is_bot:
        flask.g.is_bot = True

    # Logged-in users have passed the test already
    if publ.user.get_active():
        return

    # Send possible crawlers to the login page
    score = 0
    for item in ('id', 'tag', 'all_tags', 'date'):
        score += len(flask.request.args.getlist(item))
    if score > 1:
        raise werkzeug.exceptions.Unauthorized("Sentience test")

    return


@app.after_request
def add_webmention_endpoint(response):
    """
    This publishes a webmention endpoint for everything, including error pages
    (necessary for receiving pings to private entries) and image resources.
    Please fix the endpoint URL before uncommenting this.
    """
    # response.headers.add('link', '<https://webmention.io/DOMAIN_GOES_HERE/webmention>; rel="webmention"')
    return response


@app.path_alias_regex(r'/\.well-known/(host-meta|webfinger).*')
def redirect_bridgy(match):
    """
    This redirects ActivityPub activity to fed.brid.gy. See
    https://fed.brid.gy/#use for usage. You can follow my site
    at @beesbuzz.biz@beesbuzz.biz on Mastodon et al if you want.
    """
    return 'https://fed.brid.gy' + flask.request.full_path, False


@app.route('/_access_request/<int:entry_id>', methods=['POST'])
def access_request(entry_id: int):
    """
    This is the handler for the _unauthorized template's access request form.
    Given an impassioned plea for access to an entry, this sends an email to
    the admin of the site (their email address given in msg['To'], below) with
    the logged-in user's identity and the form contents.

    The code here leverages Authl's sendmail wrapper, just because it already
    exists. There's no particular reason to use that aside from convenience.
    It could just as well write into a database row or the like.
    """
    import publ.model
    import publ.user
    import publ.entry
    from authl.handlers.email_addr import smtplib_connector, simple_sendmail
    import email.message
    from flask import request

    from pony import orm

    with orm.db_session():
        entry_obj = publ.model.Entry.get(id=entry_id)
        if not entry_obj:
            return 400, "Missing entry"
        entry = publ.entry.Entry.load(entry_obj)

        user = publ.user.get_active()
        if not user:
            return 400, "Missing user"
        if 'no-requests' in user.groups:
            return 403, "Sorry, try again later"

        connector = smtplib_connector(
            hostname=config['auth']['SMTP_HOST'],
            port=config['auth']['SMTP_PORT'],
            username=config['auth'].get('SMTP_USERNAME'),
            password=config['auth'].get('SMTP_PASSWORD'),
            use_ssl=config['auth'].get('SMTP_USE_SSL'),
        )
        send_func = simple_sendmail(connector, config['auth']['EMAIL_FROM'],
                                    f"Access request for {user.humanize}")

        msg = email.message.EmailMessage()
        msg['To'] = 'admin@example.com.FIXME'

        if request.form['email']:
            msg['Reply-To'] = request.form['email']

        msg.set_content(
            f"""
Entry: {entry.link(absolute=True)}
Name: {request.form['name']}
Identity: {user.identity} ({user.humanize})
Email: {request.form.get('email') or "Not provided"}

{request.form.get('reason') or "No reason given"}
            """)

    send_func(msg)

    return "Message sent."


@app.route('/.well-known/atproto-did')
def did():
    """
    Want to use the website as an ATProto/bluesky identifier? Here's where
    to set that up.
    """
    # return 'did:plc:porntipsguzzardo'
