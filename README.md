# Publ sample templates

These templates are based on the ones I use on [my website](https://beesbuzz.biz). Here is some documentation on how they are put together.

This repository also contains some basic content to demonstrate parts of the site in operation. To run the sample site you can clone this repository and, inside your clone, type the following:

```bash
pipenv install
./run.sh
```

which will run the sample site at http://localhost:5000

## General overview

The root-level `index.html` and `entry.html` handle the generic layout for index and entry pages throughout the site. `feed.xml` is the Atom feed.

The provided `error.html` is just a simple default handler; my actual site also has handlers for `400`, `403`, and `404`. Each of these overrides the `flair` block within the `error` template. The `404.html` shows a tiny example of how to make 404-specific content on the error page.

`_comment_thread.html` is a template that the other templates use to insert the Disqus comment code. If you want to use this you'll need to change the `DISQUS_SHORTNAME` configuration variable. By default a page will get a thread ID of `publ_{entry-id}`, but this can be overridden with the `Thread-Id` header on the entry file (which I use for legacy entries).

`style.css` is the generic stylesheet for sections which have not overridden the stylesheet. It makes use of the `bubbly.css` and `pygments.default.css` libraries, which are stored in the `static` directory.

`robots.txt` is also a template, just to make things simpler. It links to the `sitemap.xml` template.

The `sitemap.xml` template is for search engines to have indexing hints.

`sitemap.html` is basically a human-readable site map; pretty much all it does is list out the categories on the site.

### Index template (`index.html`)

A few things of note in the `index.html` template:

* It does a relative link to `style.css` for its stylesheet; this means that it will use the dynamically-generated stylesheet for the category.
* Similarly it does a relative link to the `feed` template, so if someone points their RSS reader at a category page they only subscribe to that category (and its subcategories).
* Entries with an `Entry-Type` of `sidebar` will appear in the navigation section, rather than in the main content flow

### Feed template (`feed.xml`)

The `feed.xml` template is the Atom feed template. It uses the `_feed_entry.html` template fragment to format entries within the feed. The top-level `_feed_entry.html` is the default for the whole site.

These `_feed_entry` fragments support a custom entry header, `Spoilers`, which I use to indicate whether the below-the-fold content should be done as a link or should be put directly into the feed. For example, an entry which looks like this:

```
Title: This is a regular entry

Here is the intro text.

.....

Here is the extended text.
```

will have both paragraphs appear in the Atom feed; however, an entry like this:

```
Title: A spoilered entry
Spoilers: yes

Here is the intro text.

.....

Here is the extended text.
```

will only have the first paragraph appear in the feed, with the below-the-fold content linked to with a "Read more..." link. This behavior is controlled by the `_feed_entry.html` fragment.

Other things of note:

* It uses a recursive view; a feed for a category will also include all of the content for its subcategories
* Items with an `Entry-Type` of `sidebar` will not appear in the feed

### Entry template (`entry.html`)

Entries can override their individual stylesheet by setting a `Stylesheet` header.

Subcategories can remove comments entirely by overriding the `comments` block.

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

Given the CSS fragment generated in `index.css`, this will get its link icon with the content file `_layout/twitter.png`. It also goes ahead and sets up a path-alias such that if someone visits [/twitter](https://beesbuzz.biz/twitter) they get redirected to my Twitter page. (This is useful in that now on other pages I can simply link to `/twitter` and if I ever change my Twitter username those links will remain valid.)

The `Date` field on the link entries is simply used to order them.

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

## Comics section

This has by far the most complex layout (and unlike most of the site these templates stand alone), and there is a *lot* to take in. Let's break it down piece by piece.

### Index page (`comics/index.html`)

#### Top stuff

```
{# Filter out entries which we want to show up in the main flow #}
{% set TYPEFILTER = ['','newchapter'] %}
{% set comics = view(entry_type=TYPEFILTER,recurse=True,count=1,order="oldest" if "date" in view.spec else "newest") %}
```

This provides `TYPEFILTER` as a common list of entry types that should be treated as comics; for our purposes we're using no type and the `newchapter` type as comics.

The `comics` view includes all entries which fit that filter, including subcategories, and if the view is date-based it will sort oldest-to-newest; otherwise it retains the default newest-to-oldest sort. (This is so that when no date is specified, the default starting point will be the latest comic.)

```
{# Find all the categories visible on this page #}
{% set categories = comics.entries|groupby('category') %}
```

This sets up a `categories` grouping which is currently only used for selecting the page stylesheet; if a single series is visible it will use that series stylesheet instead of the default.

The various `macro` sections are all to make the navigation bars easier to manage; they define the following macro functions for the rest of the page:

* `navButton(size,anchor,button,alt,link,title)`: Render a navigation button, `size` pixels tall, with an image given by `_BUTTON.png`, with the provided alt text, link target, and popup (title) text. If `anchor` is specified it will be appended to the link.
* `navEntry(size, anchor, button, alt, entry)`: Make a navigation button that links to the specified entry. If `entry` is `None` the button will be `_BUTTON-disabled.png` instead of `_BUTTON.png`.
* `navView(size, anchor, button, alt, view)`: Make a navigation button that links to the provided view. It does some fancy stuff to set the title text automatically; if there's only a single comic on the view it will provide the comic name, otherwise it will give a date range.
* `navBar(size, mini, anchor)`: Render a navigation bar with the specified size and link anchor. If `mini` is specified it will omit the "latest" icon and reduce the size of less-used icons by 1/8.

Entries with an `Entry-Type` of `newchapter` will be used for the previous/next chapter links.

#### `<head>` section

If only one subcategory's comics are visible, it will use that subcategory's stylesheet; otherwise it will use the current category's. (This is mostly used to affect the title bar image.)

The page title will be the comic's title if there's only one, or a date range if there's multiple.

The generated OpenGraph card will be a square-aspect excerpt from the top or left of the comic.

#### Navigation stuff

The navigation breadcrumb trail shows the parent categories, the current category, then any subcategories. The parent categories' links will link to the current comic view in the context of that category; the subcategory links simply link to the subcategory for now.

#### Comic display

This simply displays the comics which match the `TYPEFILTER` (i.e. no type, or a type of `newchapter`). The comic itself will link to the comment page. If there is a cut, the below-cut content gets displayed below, with a thumbnail image gallery if there's images in it.

#### News box

This displays all entries with an `Entry-Type` of `News` that come after the first displayed comic and before the first comic of the next page.

### Entry page (`comics/entry.html`)

Individual entries can override their stylesheet with the `Stylesheet` entry header, if so desired. I do not actually use this function.

### Stylesheet (`comics/style.css`)

The main interesting thing about this one is that the `h1` link background gets the `_logo.jpg` from the current category's content directory if available; by default this will fall back to the `_logo.jpg` file in the comics directory instead (as part of Publ's standard image lookup rules).

