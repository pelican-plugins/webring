"""
Webring plugin for Pelican
==========================

A plugin to create a webring in your web site from a list of web feeds.
"""
from collections import namedtuple
from logging import warning
from operator import attrgetter
import re
from urllib.error import URLError
from urllib.request import Request, urlopen

from pelican import signals, utils

try:
    import feedparser
except ImportError:
    warning("Webring Plugin: Failed to load dependency (feedparser)")

WEBRING_VERSION = "0.1"
WEBRING_FEED_URLS_STR = "WEBRING_FEED_URLS"
WEBRING_MAX_ARTICLES_STR = "WEBRING_MAX_ARTICLES"
WEBRING_ARTICLES_PER_FEED_STR = "WEBRING_ARTICLES_PER_FEED"
WEBRING_SUMMARY_WORDS_STR = "WEBRING_SUMMARY_WORDS"
WEBRING_CLEAN_SUMMARY_HTML_STR = "WEBRING_CLEAN_SUMMARY_HTML"

Article = namedtuple(
    "Article",
    ["title", "link", "date", "summary", "source_title", "source_link", "source_id"],
)


def register():
    """Signal registration."""
    signals.initialized.connect(initialized)
    signals.all_generators_finalized.connect(fetch_feeds)


def initialized(pelican):
    from pelican.settings import DEFAULT_CONFIG

    DEFAULT_CONFIG.setdefault(WEBRING_FEED_URLS_STR, [])
    DEFAULT_CONFIG.setdefault(WEBRING_MAX_ARTICLES_STR, 3)
    DEFAULT_CONFIG.setdefault(WEBRING_ARTICLES_PER_FEED_STR, 1)
    DEFAULT_CONFIG.setdefault(WEBRING_SUMMARY_WORDS_STR, 20)
    DEFAULT_CONFIG.setdefault(WEBRING_CLEAN_SUMMARY_HTML_STR, True)
    if pelican:
        # Check deprecated settings
        if "WEBRING_SUMMARY_LENGTH" in pelican.settings:
            warning(
                "webring plugin: '%s' has been deprecated by '%s'",
                "WEBRING_SUMMARY_LENGTH",
                "WEBRING_SUMMARY_WORDS",
            )
        # Set default values for unset settings
        for name, value in DEFAULT_CONFIG.items():
            if name.startswith("WEBRING"):
                pelican.settings.setdefault(name, value)


def fetch_feeds(generators):
    settings = get_pelican_settings(generators)

    fetched_articles = []
    for feed_url in settings[WEBRING_FEED_URLS_STR]:
        feed_html = get_feed_html(feed_url)
        if feed_html:
            fetched_articles.extend(get_feed_articles(feed_html, feed_url, settings))

    fetched_articles = sorted(fetched_articles, key=attrgetter("date"), reverse=True)

    max_articles = settings[WEBRING_MAX_ARTICLES_STR]
    if len(fetched_articles) > max_articles:
        fetched_articles = fetched_articles[:max_articles]

    for generator in generators:
        generator.context["webring_articles"] = fetched_articles


def get_pelican_settings(generators):
    """All generators contain a reference to the Pelican settings."""
    assert len(generators) > 0
    return generators[0].settings


def get_feed_html(feed_url):
    try:
        req = Request(feed_url)
        req.add_header(
            "User-Agent",
            (
                "Webring Pelican plugin/{} "
                + "+https://github.com/pelican/pelican-plugins"
            ).format(WEBRING_VERSION),
        )
        return urlopen(req).read().decode("utf-8")
    except URLError as e:
        if hasattr(e, "reason"):
            warning(
                "webring plugin: failed to connect to feed url (%s).",
                feed_url,
                e.reason,
            )
        if hasattr(e, "code"):
            warning("webring plugin: server returned %s error (%s).", e.code, feed_url)
    except ValueError as e:
        warning("webring plugin: wrong url provided (%s).", e)


def get_feed_articles(feed_html, feed_url, settings):
    parsed_feed = feedparser.parse(feed_html)

    if parsed_feed.bozo:
        warning(
            "webring plugin: possible malformed or invalid feed (%s). " "Error=%s",
            feed_url,
            parsed_feed.bozo_exception,
        )

    articles = []
    for n, entry in enumerate(parsed_feed.entries):
        if n == settings[WEBRING_ARTICLES_PER_FEED_STR]:
            break

        published_dt = get_entry_datetime(entry)
        truncated_summary = get_entry_summary(entry, settings)

        articles.append(
            Article(
                title=entry.get("title", ""),
                link=entry.get("link", ""),
                date=published_dt,
                summary=truncated_summary,
                source_title=parsed_feed.feed.get("title", ""),
                source_link=parsed_feed.feed.get("link", ""),
                source_id=parsed_feed.feed.get("id", ""),
            )
        )

    return articles


def get_entry_datetime(entry):
    try:
        return utils.get_date(entry.get("published", ""))
    except ValueError:
        warning(
            'Webring Plugin: Invalid date on feed entry titled "%s"'
            % entry.get("title", "Unknown title")
        )
        return utils.SafeDatetime.now()


def get_entry_summary(entry, settings):
    # https://stackoverflow.com/a/12982689/11441
    def cleanhtml(raw_html):
        cleanr = re.compile("<.*?>")
        cleantext = re.sub(cleanr, "", raw_html)
        return cleantext

    summary = entry.get("description", "")

    if settings[WEBRING_CLEAN_SUMMARY_HTML_STR] > 0:
        summary = utils.truncate_html_words(
            summary, settings[WEBRING_SUMMARY_WORDS_STR]
        )

    # feedparser sanitizes html by default, but it can still contain html tags.
    if settings[WEBRING_CLEAN_SUMMARY_HTML_STR]:
        summary = cleanhtml(summary)

    return summary
