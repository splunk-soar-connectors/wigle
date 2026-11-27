# WiGLE

Publisher: Splunk <br>
Connector Version: 2.0.10 <br>
Product Vendor: WiGLE <br>
Product Name: WiGLE <br>
Minimum Product Version: 7.0.0

This app integrates with the WiGLE service to implement investigative actions

### Configuration variables

This table lists the configuration variables required to operate WiGLE. These variables are specified when configuring a WiGLE asset in Splunk SOAR.

VARIABLE | REQUIRED | TYPE | DESCRIPTION
-------- | -------- | ---- | -----------
**api_name** | required | string | API Name |
**api_token** | required | password | API Token |

### Supported Actions

[test connectivity](#action-test-connectivity) - Validate the asset configuration for connectivity. <br>
[lookup network](#action-lookup-network) - Get info about a WiFi SSID <br>
[make request](#action-make-request) - Make an HTTP request to any WiGLE API endpoint (v2 or v3) using the asset credentials.

## action: 'test connectivity'

Validate the asset configuration for connectivity.

Type: **test** <br>
Read only: **True**

Basic test for app.

#### Action Parameters

No parameters are required for this action

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failure |
action_result.message | string | | |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'lookup network'

Get info about a WiFi SSID

Type: **investigate** <br>
Read only: **True**

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**name** | required | SSID | string | `ssid` |
**max_results** | optional | Max results per page (default is 100) | numeric | |
**page_token** | optional | Page Token (Should be empty to get the 1st page) | string | `page token` |

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failure |
action_result.message | string | | |
action_result.parameter.name | string | `ssid` | |
action_result.parameter.max_results | numeric | | |
action_result.parameter.page_token | string | `page token` | |
action_result.data.\*.ssid | string | `ssid` | foobar |
action_result.data.\*.encryption | string | | wpa2 |
action_result.data.\*.city | string | | |
action_result.data.\*.region | string | | u041cu043eu0441u043au0432u0430 |
action_result.data.\*.country | string | | RU |
action_result.data.\*.bcninterval | numeric | | 0 |
action_result.data.\*.channel | numeric | | 1 |
action_result.data.\*.comment | string | | |
action_result.data.\*.dhcp | string | | ? |
action_result.data.\*.firsttime | string | | 2013-12-13T11:00:00.000Z |
action_result.data.\*.freenet | string | | ? |
action_result.data.\*.housenumber | string | | |
action_result.data.\*.postalcode | string | | 78758 |
action_result.data.\*.lasttime | string | | 2013-12-13T01:00:00.000Z |
action_result.data.\*.lastupdt | string | | 2013-12-12T23:00:00.000Z |
action_result.data.\*.name | string | | |
action_result.data.\*.netid | string | | 14:DA:E9:80:F0:8C |
action_result.data.\*.paynet | string | | ? |
action_result.data.\*.qos | numeric | | 0 |
action_result.data.\*.road | string | | |
action_result.data.\*.transid | string | | 20131213-00000 |
action_result.data.\*.trilat | numeric | | 55.728405 |
action_result.data.\*.trilong | numeric | | 37.41586685 |
action_result.data.\*.type | string | | infra |
action_result.data.\*.userfound | boolean | | True False |
action_result.data.\*.wep | string | | 2 |
action_result.data.\*.frequency | numeric | | 2412 |
action_result.data.\*.rcois | string | | 506F9A |
action_result.summary.total_results | numeric | | 5 |
action_result.summary.next_page_token | string | `page token` | 85872166 |
action_result.summary.first | numeric | | 1 |
action_result.summary.last | numeric | | 5 |
action_result.summary.result_count | numeric | | 5 |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'make request'

Make an HTTP request to any WiGLE API endpoint (v2 or v3) using the asset credentials.

Type: **generic** <br>
Read only: **False**

'make request' action for the app. Used to handle arbitrary HTTP requests with the app's asset

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**http_method** | required | The HTTP method to use for the request. | string | |
**endpoint** | required | The endpoint to send the request to. | string | |
**headers** | optional | The headers to send with the request (JSON object). An example is {'Content-Type': 'application/json'} | string | |
**query_parameters** | optional | Parameters to append to the URL (JSON object or query string). An example is ?key=value&key2=value2 | string | |
**body** | optional | The body to send with the request (JSON object). An example is {'key': 'value', 'key2': 'value2'} | string | |
**timeout** | optional | The timeout for the request in seconds. | numeric | |
**verify_ssl** | optional | Whether to verify the SSL certificate. Default is True. | boolean | |

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failure |
action_result.message | string | | |
action_result.parameter.http_method | string | | |
action_result.parameter.endpoint | string | | |
action_result.parameter.headers | string | | |
action_result.parameter.query_parameters | string | | |
action_result.parameter.body | string | | |
action_result.parameter.timeout | numeric | | |
action_result.parameter.verify_ssl | boolean | | |
action_result.data.\*.status_code | numeric | | 200 404 500 |
action_result.data.\*.response_body | string | | {"key": "value"} |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

______________________________________________________________________

Auto-generated Splunk SOAR Connector documentation.

Copyright 2026 Splunk Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and limitations under the License.
