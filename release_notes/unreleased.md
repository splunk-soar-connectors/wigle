**Unreleased**

* Migrated to the Splunk SOAR SDK 7.3.0, preserving connectivity and network lookup table output.
* Requires SOAR 7.0.0 or later with Python 3.13 or 3.15. Python 3.9 is no longer supported.
* Network lookup now prefers WiGLE's `searchAfter` cursor and falls back to the legacy `search_after` field. `action_result.summary.next_page_token` is now a string. Pass it directly to `page_token`, and update playbooks that compare it as a number. Previously stored integer cursors are still accepted as input.
* Network lookup rejects `max_results` outside 1 to 1000 before making a request. Standard API accounts are limited to 100 results per page.
