**Unreleased**

* Converted the app to the Splunk SOAR SDK (Python 3.13+)
* The minimum supported SOAR version is now 7.0.0
* New 'make request' action to call any WiGLE API endpoint (v2 or v3) with the asset credentials
* lookup network: added the documented 'frequency' and 'rcois' output fields
* lookup network: action_result.summary.next_page_token is now a string so it can be passed back into the page_token parameter
* lookup network: a max_results value of zero or less now fails before calling WiGLE
* lookup network: page_token also accepts a numeric value (e.g. a chained next_page_token)
