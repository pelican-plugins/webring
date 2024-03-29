CHANGELOG
=========

1.4.0 - 2023-01-27
------------------

- Retrieve feeds from configured URLs in parallel using threads (implements #9).

1.3.0 - 2021-04-03
------------------

- Fix #11 (AttributeError accessing `date` entry attribute).
- Update Webring User Agent version.
- Update `feedparser` to 6.x.

1.2.0 - 2020-08-25
------------------

- Update Pelican version to 4.5 which implements the new plugin system (#2).
- Deprecate WEBRING_SUMMARY_LENGTH in favor of WEBRING_SUMMARY_WORDS, which
  works with words instead of characters. If set to 0, truncation is disabled
  (#8).
- Improve documentation explaining how to use the plugin to create a feed
  aggregation page.

1.0.0 - 2019-11-28
------------------

Initial release as versioned package distribution.
