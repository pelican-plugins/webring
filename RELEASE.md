Release type: minor

- Update Pelican version to 4.5 which implements the new plugin system (#2).
- Deprecate WEBRING_SUMMARY_LENGTH in favor of WEBRING_SUMMARY_WORDS, which
  works with words instead of characters. If set to 0, truncation is disabled
  (#8).
- Improve documentation explaining how to use the plugin to create a feed
  aggregation page.
