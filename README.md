# Webring

[![Build Status](https://img.shields.io/github/actions/workflow/status/pelican-plugins/webring/main.yml?branch=main)](https://github.com/pelican-plugins/webring/actions)
[![PyPI Version](https://img.shields.io/pypi/v/pelican-webring)](https://pypi.org/project/pelican-webring/)

This Pelican plugin adds a webring or feed aggregation to your site from a list
of web feeds.

It retrieves the latest posts from a list of web feeds and makes them available
in templates, effectively creating a [partial webring][1] or feed aggregation.
Posts are sorted from newer to older.

It is inspired by [openring](https://git.sr.ht/~sircmpwn/openring), a tool for
generating an HTML file to include in your [SSG][2] from a template and a list
of web feeds, and
[pelican-planet](https://framagit.org/bochecha/pelican-planet), a Pelican
plugin for creating feed aggregations.

Installation
------------

This plugin can be installed via:

    python -m pip install pelican-webring

Settings
--------

```
WEBRING_FEED_URLS = []
```
A list of web feeds in the form of a URL or local file.

```
WEBRING_MAX_ARTICLES = 3
```
The maximum number of articles.

```
WEBRING_ARTICLES_PER_FEED = 1
```
The maximum number of articles per feed.

```
WEBRING_SUMMARY_WORDS = 20
```
The maximum number of words of post summaries. If set to 0, truncation is
disabled.

```
WEBRING_CLEAN_SUMMARY_HTML = True
```
Whether to clean html tags from post summaries or not.

**Example**

Let's suppose we have two blogs in our webring and want to show two articles
per blog. We would also like to show a quite short summary.

```
WEBRING_FEED_URLS = [
    'https://justinmayer.com/feeds/all.atom.xml',
    'https://danluu.com/atom.xml'
]
WEBRING_ARTICLES_PER_FEED = 2
WEBRING_MAX_ARTICLES = 4
WEBRING_SUMMARY_LENGTH = 25
```

Templates
---------

The plugin makes available the resulting web feed articles in the variable
`webring_articles`.

All existing _date_ attributes are Pelican `utils.SafeDatetime` objects, which
can be used with [Pelican's Jinja filter
`strftime`](https://docs.getpelican.com/en/stable/themes.html#date-formatting).

Each article contains all available properties in the original feed entry, for
example:

- `article.title`: The article title.
- `article.link`: The article URL.
- `article.date`: The article date as a Pelican `utils.SafeDatetime` object.
- `article.summary`: The article summary, as provided in the web feed and modified
according to this plugin's settings.
- `article.description`: The original article summary, without cleaning or
  truncation.

Articles also contain information about the _source feed_, which can be
accessed through `source_` prefixed attributes:

- `source_title`: The title of the web feed.
- `source_link`: A link to the web feed.
- `source_id`: An identification field provided in some web feeds.

If you access an attribute that is not present in the entry or source feed, an
empty string will be returned, except for _dates_ (`published`, `updated`,
`created` and `expired`) that `None` is returned.

For a list of available entry and source feed attributes, [read the feedparser
reference document](https://pythonhosted.org/feedparser/reference.html).

You can use `webring_articles` in any kind of content type, including _pages_
and _articles_. Read the following sections for examples on how to use this
variable in your templates.

### Adding a Webring section in the bottom of articles

Imagine we'd like to put our webring in the bottom of articles, using the
default Pelican template (ie. notmyidea). To simplify, we'll use the existing
CSS classes.

Edit the `notmyidea/templates/base.html` file and make it look like this:

```
        ...
        <section id="extras" class="body">
        {% if WEBRING_FEED_URLS %}
            <div class="webring">
                <h2>Webring</h2>
                {% for article in webring_articles %}
                <p><a href="{{ article.link }}">{{ article.title }}</a></p>
                <p>{{ article.date|strftime('%d %B %Y') }} - {{ article.summary}}</p>
                {% endfor %}
            </div>
        {% endif %}
        {% if LINKS %}
        ...
```

If there were no links or social widgets, the result would be like in the
image below:

![Footer Webring](https://github.com/pelican-plugins/webring/raw/main/webring-footer.jpg)

### Adding a feed aggregation page

In this case, we'd like to generate a new page with all feed contents processed
by this plugin. For example, imagine we'd like to access that page as:
`https://my-domain.com/feed-aggregation`.

This objective can be accomplished in several ways in Pelican. We're showing
here one that only requires a new HTML template.

The following is an example template file named `feed-aggregation.html` based on
`page.html` that should reside in your theme template directory:

```
{% extends "base.html" %}
{% block title %}Feed aggregation{% endblock %}

{% block content %}
<section id="content" class="body">
    <h1 class="entry-title">Feed aggregation</h1>

    {% if WEBRING_FEED_URLS %}
        {% for article in webring_articles %}
            <article class="hentry">
                <header>
                    <h2><a href="{{ article.link }}">{{ article.title }}</a></h2>
                </header>
                <p>{{ article.date|strftime('%d %B %Y') }}</p>
                <div class="entry-content">
                {{ article.summary}}
                </div>
            </article>
        {% endfor %}
    {% endif %}

</section>
{% endblock %}
```

Finally, in order for our template to be rendered in the wanted location, we add the following **template page** to our `pelicanconf.py`. Note that `feed-aggregation.html` is relative to your theme's template directory.

```
TEMPLATE_PAGES = { 'feed-aggregation.html': 'feed-aggregation/index.html' }
```

The final result would be as in the image below:

![Page Webring](https://github.com/pelican-plugins/webring/raw/main/webring-page.jpg)

Contributing
------------

Contributions are welcome and much appreciated. Every little bit helps. You can contribute by improving the documentation, adding missing features, and fixing bugs. You can also help out by reviewing and commenting on [existing issues][].

To start contributing to this plugin, review the [Contributing to Pelican][] documentation, beginning with the **Contributing Code** section.

[existing issues]: https://github.com/pelican-plugins/webring/issues
[Contributing to Pelican]: https://docs.getpelican.com/en/latest/contribute.html
[1]: https://en.wikipedia.org/wiki/Webring "In a proper webring, websites would be linked in a circular structure."
[2]: https://en.wikipedia.org/wiki/Category:Static_website_generators "Static Site Generator"
