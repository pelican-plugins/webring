"""
Webring plugin for Pelican
==========================

A plugin to create a webring or feed aggregation in your web site from a list
of web feeds.
"""
import concurrent.futures
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

WEBRING_VERSION = "1.3.0"
WEBRING_FEED_URLS_STR = "WEBRING_FEED_URLS"
WEBRING_MAX_ARTICLES_STR = "WEBRING_MAX_ARTICLES"
WEBRING_ARTICLES_PER_FEED_STR = "WEBRING_ARTICLES_PER_FEED"
WEBRING_SUMMARY_WORDS_STR = "WEBRING_SUMMARY_WORDS"
WEBRING_CLEAN_SUMMARY_HTML_STR = "WEBRING_CLEAN_SUMMARY_HTML"


class Article:
    def __init__(
        self, entry: feedparser.FeedParserDict, source: feedparser.FeedParserDict
    ):
        self._entry = entry
        self._source = source

    def __getattr__(self, key):
        """Lazy build special attributes"""
        try:
            if key.startswith("source_"):
                entry_id = key.partition("_")[2]
                return self._source[entry_id]
            elif key in ["published", "updated", "created", "expired"]:
                return get_entry_datetime(key, self._entry)
            elif key == "summary":
                return get_entry_summary(self._entry)
            elif key == "date":
                # If 'date' is not present, use 'published' for compatibility with old
                # webring versions (<1.2.0).
                key = key if key in self._entry else "published"
                return get_entry_datetime(key, self._entry)
            else:
                return self._entry[key]
        except KeyError:
            return ""


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
    # save global settings
    global settings
    settings = pelican.settings if pelican else DEFAULT_CONFIG


def fetch_feeds(generators):
    fetched_articles = []

    def fetch(feed_url):
        feed_html = get_feed_html(feed_url)
        if feed_html:
            return get_feed_articles(feed_html, feed_url)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for feed_url in settings[WEBRING_FEED_URLS_STR]:
            futures.append(executor.submit(fetch, feed_url=feed_url))
        for future in concurrent.futures.as_completed(futures):
            articles = future.result()
            if articles is not None:
                fetched_articles.extend(articles)

    fetched_articles = sorted(fetched_articles, key=attrgetter("date"), reverse=True)

    max_articles = settings[WEBRING_MAX_ARTICLES_STR]
    if len(fetched_articles) > max_articles:
        fetched_articles = fetched_articles[:max_articles]

    for generator in generators:
        generator.context["webring_articles"] = fetched_articles


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


def get_feed_articles(feed_html, feed_url):
    parsed_feed = feedparser.parse(feed_html)

    if parsed_feed.bozo:
        warning(
            "webring plugin: possible malformed or invalid feed (%s). " "Error=%s",
            feed_url,
            parsed_feed.bozo_exception,
        )

    max_articles = settings[WEBRING_ARTICLES_PER_FEED_STR]
    return [Article(e, parsed_feed.feed) for e in parsed_feed.entries[:max_articles]]


def get_entry_datetime(key, entry):
    try:
        # Empty string raises ValueError in dateutil.parser.parse()
        return utils.get_date(entry.get(key, ""))
    except ValueError:
        warning(
            "Webring Plugin: Invalid '%s' on feed entry titled '%s'",
            key,
            entry.get("title", "Unknown title"),
        )
        return None


def get_entry_summary(entry):
    # https://stackoverflow.com/a/12982689/11441
    def cleanhtml(raw_html):
        cleanr = re.compile("<.*?>")
        cleantext = re.sub(cleanr, "", raw_html)
        return cleantext

    try:
        # this will get the first of 'summary' and 'subtitle'
        summary = entry["description"]
    except KeyError:
        summary = ""

    if settings[WEBRING_CLEAN_SUMMARY_HTML_STR] > 0:
        summary = utils.truncate_html_words(
            summary, settings[WEBRING_SUMMARY_WORDS_STR]
        )

    # feedparser sanitizes html by default, but it can still contain html tags.
    if settings[WEBRING_CLEAN_SUMMARY_HTML_STR]:
        summary = cleanhtml(summary)

    return summary
