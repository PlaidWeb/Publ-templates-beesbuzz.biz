# Publ templates for http://beesbuzz.biz/

These templates are based on the ones I use on [my website](https://beesbuzz.biz). Here is some documentation on how they are put together.

This repository also contains some basic content to demonstrate parts of the site in operation.

To run the sample site, you can do the following:

1. Install [Python](https://python.org/) (at least version 3.6) and [Poetry](https://python-poetry.org/)
2. Clone this repository
3. Run `run.sh` (Linux, macOS, WSL, Cygwin) or `winrun.cmd` (Windows)
4. Point a browser to `http://localhost:5000`

See the [Publ getting started guide](https://publ.plaidweb.site/manual/328-Getting-started) for more thorough setup instructions.

## App setup

The application lives in `app.py`, which is set up with basic logging and the following facets:

### Run scripts

The `run.sh` script installs the current package versions (namely Publ and its dependencies) and indexes all new content (`flask publ reindex`).

The `fix_dates.py` script goes through and renames my content files to make them easier to find based on date and/or entry ID, and also makes it obvious if I've forgotten about a draft entry or if an entry's been deleted. As of Publ v0.7.4 a similar thing can be done as a Publ built-in with e.g.

```sh
poetry run flask normalize -a
```

but I don't especially like changing the filenames quite so substantially.

### Publ configuration

The database is just local SQLite (yes, even in production; it's actually faster than MySQL or Postgres!).

If running in debug, there is no cache, otherwise it uses a memcached running on localhost. The cache itself doesn't really do much to speed up the site (as the hit rate is pretty low most of the time), but it does help to  mitigate heavy load spikes whenever Hacker News decides to pay me a visit or whatever.

The index gets a rescan once a day, which is probably not necessary but it doesn't hurt anything either.

### Authentication

For friends-only/private entries, this sample site is configured to support emailed magic links (using the local mail server), Mastodon, and IndieAuth; `test:` URLs are also available when the site is running in debug mode. If you have a Twitter API key you can also set the `TWITTER_CLIENT_KEY` and `TWITTER_CLIENT_SECRET` environment variables accordingly, and then people can sign in with Twitter as well.

### Routing rules

`/favicon.ico` redirects to `/static/favicon.ico`. This could also have been done using `send_file('favicon.ico')` in the current directory to make this more transparent, but it doesn't really matter.

Legacy comics paths like `/d/20060606.php` get redirected to an appropriate date-based view within `/comics/`.

Missing blog entries (which I haven't ported from my old site) get redirected to [a placeholder apology](https://beesbuzz.biz/7821).

ActivityPub requests are redirected to [bridgy fed](https://fed.brid.gy), which serves as a proxy for the ActivityPub identity `@beesbuzz.biz@beesbuzz.biz`. The intention was to support directly publishing my content to subscribers on Mastodon but the experience there isn't great, due to a fairly large impedance mismatch. Oh well.

## Template overview

The root-level `index.html` and `entry.html` handle the generic layout for index and entry pages throughout the site. `feed.xml` is the Atom feed.

The provided `error.html` is just a simple default handler; my actual site also has handlers for `400`, `403`, and `404`. Each of these overrides the `flair` block within the `error` template. The `404.html` in this repository shows a tiny example of how to make 404-specific content on the error page.

`style.css` is the generic stylesheet for sections which have not overridden the stylesheet. It makes use of the `bubbly.css` and `pygments.default.css` libraries, which are stored in the `static` directory.

`robots.txt` is also a template, just to make things simpler. It links to the `sitemap.xml` template.

The `sitemap.xml` template is for search engines to have indexing hints.

`sitemap.html` is basically a human-readable site map; pretty much all it does is list out the categories on the site.

### Index template (`index.html`)

A few things of note in the `index.html` template:

* It does a relative link to `style.css` for its stylesheet; this means that it will use the dynamically-generated stylesheet for the category.
* Similarly it does a relative link to the `feed` template, so if someone points their RSS reader at a category page they only subscribe to that category (and its subcategories).
* Entries with an `Entry-Type` of `sidebar` will appear in the navigation section, rather than in the main content flow

#### Articles extensions (`articles/index.html`)

If an entry has a `Cut` header it will put the cut text next to the "read more" link. This is useful for providing content warnings or the like.

### Feed template (`feed.xml`)

The `feed.xml` template is the Atom feed template. It uses the `_feed_entry.html` template fragment to format entries within the feed. The top-level `_feed_entry.html` is the default for the whole site.

These `_feed_entry` fragments support a custom entry header, `Cut`, which I use to indicate whether the below-the-fold content should be done as a link or should be put directly into the feed. For example, an entry which looks like this:

```
Title: This is a regular entry

Here is the intro text.

.....

Here is the extended text.
```

will have both paragraphs appear in the Atom feed; however, an entry like this:

```
Title: A spoilered entry
Cut: yes

Here is the intro text.

.....

Here is the extended text.
```

will only have the first paragraph appear in the feed, with the below-the-fold content linked to with a "Read more..." link. This behavior is controlled by the `_feed_entry.html` fragment.

Other things of note:

* It uses a recursive view; a feed for a category will also include all of the content for its subcategories
* Items with an `Entry-Type` of `sidebar` will not appear in the feed
* Items with response-type microformat headers (`in-reply-to`, `bookmark-of`, `like-of`, `rsvp`) will not appear unless there's a URL parameter of `push=1`

### Entry template (`entry.html`)

Entries can override their individual stylesheet by setting a `Stylesheet` header.

Entries with a `cut` will display the extended text inside a `<details>`, with the cut text as the `<summary>`. This is to give fair warning to folks who are linked directly to the entry from the outside or who are navigating between adjacent entries.

Comments can be disabled on an individual entry by setting a `Disable-Comments` header, e.g.

```
Title: Please don't reply to this post
Disable-Comments: asdf
```

#### Webmention support

There are some custom reply-context headers for this template for better outgoing [Webmention](http://indieweb.org/Webmention) support:

* Like-of: Indicates that this entry "likes" the specified URL
* In-reply-to: Indicates that this entry is a reply to the specified URL
* Repost-of: Indicates that this entry is a repost of the specified URL
* Bookmark-of: Indicates that this entry collects the specified URL as a resource
* Mention-of: Indicates that this entry simply mentions the URL (this is also implied without a header though)
* RSVP: Indicates that this entry is a response to an invitation. In this case, after the URL you provide an RSVP disposition, such as `yes`, `no`, or `maybe`. For example:

    ```
    RSVP: http://example.com/cool-party yes
    RSVP: http://example.com/bad-party no
    ```

In general you should only have one reply context header; more than one is *technically* supported but it can cause weird things to happen.

The entry template includes [`_webmention.html`](#incoming-webmention) for incoming webmention support.

#### Per-category extensions (`(category)/entry.html`)

Several of the categories override parts of the master `entry.html`, primarily to change the way that images are displayed by default.

Subcategories can remove comments entirely by overriding the `comments` block, although no categories currently do this.

## Main/landing page (`_mainpage.html`, `index.css`)

The landing page for the site is handled by the `_mainpage.html` template; this is selected by there being a content file called `_site.cat` (this filename is arbitrary) with the following content:

```
Name: busybee
Index-Template: _mainpage
Path-Alias: /feeds.php feed

Graphic design, music production, and blogging tools. The web of yesterday, tomorrow!
```

This configures the name of the root category to be "busybee," maps the index page to the `_mainpage` template (this could also be specified as `_mainpage.html`), and it maps a legacy URL for the RSS feed from my old site to the `feed` template.

`_mainpage.html` references `index.css` as its stylesheet. This stylesheet template is only intended to be used from the main page; while it can load from other categories it doesn't actually do anything useful (and it's harmless if some random person decides to poke around with it).

`index.css` does some fancy logic; in particular, for all of the top-level entries with an `Entry-Type` of `sidebar`, it generates a CSS fragment for its link icon. For example, my Twitter link icon has the following entry file associated with it:

```
Title: @fluffy
Icon: twitter
Entry-Type: sidebar
Redirect-To: https://twitter.com/fluffy
Date: 200
Entry-ID: 4329
UUID: bfec3987-2754-47b0-b6f5-0231b1b35672
Path-Alias: /twitter
```

Given the CSS fragment generated in `index.css`, this will get its link icon with the content file `_layout/twitter.png`. It also goes ahead and sets up a path-alias such that if someone visits [/twitter](https://beesbuzz.biz/twitter) they get redirected to my Twitter page. (This is useful in that now on other pages I can simply link to `/twitter` and if I ever change my Twitter username for some reason -- [unlikely as that is](https://twitter.com/fluffy/status/1140411704414621696) -- those links will remain valid.)

The sidebar is sorted using the `Sort-Title` attribute.

The `#categories li.{{cat.basename}}` rule works similarly to the link fragments; it simply generates CSS rules for each top-level site category where the background image is set to, for example, `_layout/cat-comics.jpg`.

## Art section

This section is notable in that it has a few different layout overrides; for example, `drawings/style.css` changes the layout of the thumbnails on the page, and `photography/entry.html` suppresses the index-page thumbnail. A typical photography entry looks like this:

```
Title: Astoria
Path-Alias: /art/photography/astoria.php
Category: art/photography
Date: 2018-04-29 23:26:14-07:00
Entry-ID: 18
UUID: b3c6f3cd-16fc-4cf2-b165-8a059e66d052

![](DSC06786.jpg) Photos in and around Astoria, OR, centered around the [iLLuMiNART festival](https://www.facebook.com/1928Ratrod/)

.....

![](DSC06750.jpg
|DSC06754.jpg
|DSC06786.jpg
|IMG_4332.jpg
|IMG_4334.jpg
|etc...
)
```

## Comment forms (`_comment_thread.html`)

I currently use [Isso](https://posativ.org/isso/), which is a Disqus-like self-hosted comment system. If you can run Publ on your site you can also run Isso, although the setup is a bit complicated and outside the scope of this writeup.

`_comment_thread.html` is a template that the other templates use to insert the comment embed code. If you want to use this you'll need to change the thread ID generation and the Isso instance URL accordingly. You will also probably want to implement [`app.thread_id`](app.py#L87) so that you can provide [private, signed thread URIs](http://beesbuzz.biz/blog/4678-Proper-comment-privacy-Yay).

If you need to update the thread ID key, you can run the script `update-thread-ids.py` against the Isso database.

Also, the `migrations/` directory contains a few random comment-migration scripts that others might find useful, although keep in mind that this is for preservation of data going back to 2003:

* `disqus-import.py`: Imports threads from Disqus, using the named Disqus thread ID mapping (rather than the page-URI-based scheme that the Isso importer uses)
* `import-mt.py`: Converts legacy Movable Type comment threads to Isso threads; assumes that the entries have a `Thread-ID: mt_NNNNN` header (where `NNNNN` is the Movable Type entry ID)
* `import-mt-specific.py`: Transfers MT comment threads that weren't mapped correctly due to various things (for example, in my journal comics, many of them were originally posted on my blog before I had a comics section and I never got around to migrating *those* comments either)
* `reimport-phpbb.py`: Imports comments from phpBB (using `phpbb_integrate`, my ancient system for [shoehorning phpBB 2.x into Movable Type](http://web.archive.org/web/20121014130936/http://beesbuzz.biz/blog/e/2003/10/24-phpbb-integrate.php))
* `unmangle.py`: Try to unmangle some of the weirder artifacts from the many layers of phpBB &rarr; Disqus &rarr; Isso

For all the above cases I had converted database dumps from MySQL to SQLite using [mysql2sqlite](https://github.com/dumblob/mysql2sqlite).

### Use with Disqus

When I used Disqus, my `_comment_thread.html` template looked something like this:

```html
<div id="disqus_thread"></div>
<script>
    var disqus_config = function () {
        this.page.url = "{{entry.permalink(absolute=True)}}";  // Replace PAGE_URL with your page's canonical URL variable
        /* {# NOTE: this doesn't lend itself well to privacy since it makes thread IDs very easy to guess; see the note in README.md #} */
        this.page.identifier = "{{entry.get('Thread-ID', 'publ_' ~ entry.id)}}"; // Replace PAGE_IDENTIFIER with your page's unique identifier variable
    };
    (function() {  // DON'T EDIT BELOW THIS LINE
        var d = document, s = d.createElement('script');

        s.src = 'https://[DISQUS-SHORTNAME}.disqus.com/embed.js';

        s.setAttribute('data-timestamp', +new Date());
        (d.head || d.body).appendChild(s);
    })();
</script>
<noscript>Please enable JavaScript to view the <a href="https://disqus.com/?ref_noscript" rel="nofollow">comments powered by Disqus.</a></noscript>
```

However, Disqus was [pretty bad for private entries](http://beesbuzz.biz/blog/1768-Moving-away-from-Disqus), so I moved away from it. As a partial mitigation for one of the privacy concerns I had been using an ad-hoc mechanism to obscure the Disqus thread IDs, but it was ultimately ineffective. If you care about privacy, don't use Disqus. Currently I use [isso](https://posativ.org/isso/), but at some point I will probably build a more purpose-specific commenting system.

## <span id="incoming-webmention">Incoming webmentions (`/_webmention.html`, `/static/webmention.js`)</span>

Incoming webmentions are displayed via [webmention.js](https://github.com/PlaidWeb/webmention.js).

Entries can register additional source URLs using one or more `Old-URL` headers, e.g.:

```
Title: This title has changed
Entry-ID: 1234
Old-URL: https://blog.example.com/blog/1234-This-is-the-old-title
```

## Comics section

This has by far the most complex layout (and unlike most of the site these templates stand alone, aside from the Atom feed), and there is a *lot* to take in. Let's break it down piece by piece.

### Index page (`comics/index.html`)

#### Top stuff

```
{# Filter out entries which we want to show up in the main flow #}
{% set TYPEFILTER = [''] %}
{% set comics = view(entry_type=TYPEFILTER,recurse=True,count=1,order="oldest" if "date" in view.spec else "newest") %}
```

This provides `TYPEFILTER` as a common list of entry types that should be treated as comics; currently that is just the empty/default type. (Previously there was a separate type for `newchapter` back before Publ had a tagging system.)

The `comics` view is restricted to entries that fit the type filter, and includes all subcategories. `count=1` means it will only show the most recent comic unless there's a date filter in place (as date filters take priority over count-based pagination). If there is a date specified in the default view, it will sort oldest-to-newest so they appear in reading order; otherwise they appear newest-to-oldest so that the most recent comic will display by default.

(This could probably be better.)

```
{# Find all the categories visible on this page #}
{% set categories = comics.entries|groupby('category') %}
```

This sets up a `categories` grouping which is currently only used for selecting the page stylesheet; if a single series is visible it will use that series stylesheet instead of the default. The stylesheet mostly just chooses which image to put inside the heading.

The various `macro` sections are all to make the navigation bars easier to manage; they define the following macro functions for the rest of the page:

* `navButton(size,anchor,button,alt,link,title)`: Render a navigation button, `size` pixels tall, with an image given by `_BUTTON.png`, with the provided alt text, link target, and popup (title) text. If `anchor` is specified it will be appended to the link.
* `navEntry(size, anchor, button, alt, entry)`: Make a navigation button that links to the specified entry. If `entry` is `None` the button will be `_BUTTON-disabled.png` instead of `_BUTTON.png`.
* `navView(size, anchor, button, alt, view)`: Make a navigation button that links to the provided view. It does some fancy stuff to set the title text automatically; if there's only a single comic on the view it will provide the comic name, otherwise it will give a date range.
* `navBar(size, mini, anchor)`: Render a navigation bar with the specified size and link anchor. If `mini` is specified it will omit the "latest" icon and reduce the size of less-used icons by 1/8.

Entries with a tag of `newchapter` will be used for the previous/next chapter links. I use the `Hidden-Tag` variant, so that if I ever get around to adding browseable tags these won't be visible.

#### `<head>` section

If only one subcategory's comics are visible, it will use that subcategory's stylesheet; otherwise it will use the current category's. (This is mostly used to affect the title bar image.)

The page title will be the comic's title if there's only one, or a date range if there's multiple.

The generated OpenGraph card will be a square-aspect excerpt from the top or left of the comic. If there's a CW cut on the entry it'll also get downsized to 32x32 to make it blurry.

#### Navigation stuff

The navigation breadcrumb trail shows the parent categories, the current category, then any subcategories. The parent categories' links will link to the current comic view in the context of that category; the subcategory links simply link to the subcategory for now (as the current comic might not exist within the subcategory).

#### Comic display

This simply displays the comics which match the `TYPEFILTER`. The comic itself will link to the comment page. If there is extended text, the below-cut content gets displayed below, with a thumbnail image gallery if there's images in it.

Also, if the entry has a `Cut` header (for a content warning or the like), the comic will display inside a collapsed `<details>` box, to allow people to use their discretion in looking at it.

#### News box

This displays all entries with an `Entry-Type` of `News` that come after the first displayed comic and before the first comic of the next page.

### Entry page (`comics/entry.html`)

Individual entries can override their stylesheet with the `Stylesheet` entry header, if so desired. I do not actually use this function.

CW cuts work similarly to the index page; the comic will be hidden behind a `<details>`, and the OpenGraph image excerpt will be blurred.

### Stylesheet (`comics/style.css`)

The main interesting thing about this one is that the `h1` link background gets the `_logo.jpg` from the current category's content directory if available; by default this will fall back to the `_logo.jpg` file in the comics directory instead (as part of Publ's standard image lookup rules).


## Other configuration/scripts

I have configured my site to be deployed via a [git hook](http://publ.beesbuzz.biz/manual/deploying/441-Continuous-deployment-with-git), and I send out WebSub and Webmention pings using [Pushl](https://github.com/PlaidWeb/Pushl).

### `pushl.sh`

This script runs `pushl` on my various feeds in order to push out webmentions to other sites. My own feeds have a `?push=1` parameter so that response-type entries appear.

### `pub.sh`

This is a quick-and-dirty script for generating stub entries for webmention responses. It's a bit fiddly but it lets me use Publ to more easily respond to other things using IndieWeb, as well as on Mastodon via [Bridgy Fed](https://fed.brid.gy). For example, if I want to "like" a post I can say:

```
./pub.sh like-of https://beesbuzz.biz/blog/7950-Things-I-accomplished-today
```

or if I want to reply I can say:

```
vi $(./pub.sh in-reply-to https://beesbuzz.biz/blog/7950-Things-I-accomplished-today)
```

and then fill in the entry body.
