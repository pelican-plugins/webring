"""Tests for webring plugin

Test Atom and RSS feeds have been generated using Pelican itself using the
contents of its `samples/content` folder.
"""
from collections import Counter
from operator import attrgetter, itemgetter
import os
from types import SimpleNamespace
import unittest

from pelican import utils
from pelican.generators import Generator
from pelican.settings import DEFAULT_CONFIG
from pelican.tests.support import get_context, get_settings, module_exists

import webring


class NullGenerator(Generator):
    pass


@unittest.skipUnless(module_exists("feedparser"), "install feedparser module")
class WebringTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generators = [NullGenerator(get_context(), get_settings(), "", "", "")]
        cls.settings = cls.generators[0].settings
        cls.pelican = SimpleNamespace()
        cls.pelican.settings = cls.settings

    def setUp(self):
        self.reset_settings()
        self.set_feeds()
        webring.initialized(self.pelican)

    def reset_settings(self):
        for name, value in self.settings.items():
            if name.startswith("WEBRING"):
                self.settings[name] = DEFAULT_CONFIG[name]

    def feed_url(self, feed_type):
        test_data_path = os.path.join(os.path.dirname(__file__), "test_data")
        return "file://" + os.path.join(test_data_path, f"pelican-{feed_type}.xml")

    def set_feeds(self, feeds=None):
        default = [self.feed_url("rss"), self.feed_url("atom")]
        self.settings[webring.WEBRING_FEED_URLS_STR] = (
            default if feeds is None else feeds
        )

    def get_fetched_articles(self):
        return self.generators[0].context["webring_articles"]

    def test_max_articles(self):
        webring.fetch_feeds(self.generators)
        articles = self.get_fetched_articles()
        self.assertLessEqual(
            len(articles), self.settings[webring.WEBRING_MAX_ARTICLES_STR]
        )

    def test_articles_per_feed(self):
        self.settings[webring.WEBRING_MAX_ARTICLES_STR] = 6
        self.settings[webring.WEBRING_ARTICLES_PER_FEED_STR] = 3
        webring.fetch_feeds(self.generators)
        articles = self.get_fetched_articles()
        feed_counts = Counter(a.source_id for a in articles)
        self.assertEqual(list(map(itemgetter(1), feed_counts.items())), [3, 3])

    def test_common_attributes(self):
        """These are attributes present in ALL articles in both RSS and Atom test feeds.
        Optional attributes are not checked.
        """
        webring.fetch_feeds(self.generators)
        articles = self.get_fetched_articles()
        for a in articles:
            self.assertIsInstance(a.published, utils.SafeDatetime)
            self.assertIsInstance(a.updated, utils.SafeDatetime)
            self.assertEqual(a.date, a.published)
            self.assertEqual(a.created, None)
            self.assertEqual(a.expired, None)
            self.assertNotEqual(a.author, "")
            self.assertNotEqual(a.link, "")
            self.assertNotEqual(a.id, "")
            self.assertNotEqual(a.summary, "")
            self.assertNotEqual(a.source_title, "")
            self.assertNotEqual(a.source_link, "")

    def test_common_atom_attributes(self):
        self.set_feeds([self.feed_url("atom")])
        webring.fetch_feeds(self.generators)
        articles = self.get_fetched_articles()
        for a in articles:
            self.assertNotEqual(a.source_id, "")

    def test_invalid_entry_attribute(self):
        webring.fetch_feeds(self.generators)
        articles = self.get_fetched_articles()
        self.assertEqual(articles[0].invalid_attribute, "")

    def test_clean_summary(self):
        webring.fetch_feeds(self.generators)
        articles = self.get_fetched_articles()
        summaries = list(map(attrgetter("summary"), articles))
        self.assertTrue(all(s.find("<") < 0 for s in summaries))

    def test_dont_clean_summary(self):
        self.settings[webring.WEBRING_CLEAN_SUMMARY_HTML_STR] = False
        webring.fetch_feeds(self.generators)
        articles = self.get_fetched_articles()
        summaries = list(map(attrgetter("summary"), articles))
        self.assertTrue(all(s.find("<") >= 0 for s in summaries))

    def test_summary_length(self):
        self.settings[webring.WEBRING_SUMMARY_WORDS_STR] = 3
        webring.fetch_feeds(self.generators)
        articles = self.get_fetched_articles()
        self.assertTrue(all(len(a.summary) <= 30 for a in articles))

    def test_long_summary_length(self):
        self.settings[webring.WEBRING_SUMMARY_WORDS_STR] = 100
        webring.fetch_feeds(self.generators)
        articles = self.get_fetched_articles()
        self.assertTrue(not any(a.summary.endswith("…") for a in articles))

    def test_summary_disabled(self):
        self.settings[webring.WEBRING_SUMMARY_WORDS_STR] = 0
        webring.fetch_feeds(self.generators)
        articles = self.get_fetched_articles()
        self.assertFalse(any(a.summary.endswith("…") for a in articles))

    def test_malformed_url(self):
        self.set_feeds(["://pelican-atom.xml"])
        webring.fetch_feeds(self.generators)
        self.assertEqual(len(self.get_fetched_articles()), 0)


if __name__ == "__main__":
    unittest.main()
