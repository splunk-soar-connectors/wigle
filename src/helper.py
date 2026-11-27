# Copyright (c) 2018-2026 Splunk Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language governing permissions
# and limitations under the License.
from typing import Any

import requests
from bs4 import BeautifulSoup
from soar_sdk.exceptions import ActionFailure

from .consts import DEFAULT_REQUEST_TIMEOUT, WIGLE_BASE_URL


def _process_empty_response(response: requests.Response) -> dict[str, Any]:
    if response.status_code == 200:
        return {}
    raise ActionFailure("Empty response and no information in the header")


def _process_html_response(response: requests.Response) -> dict[str, Any]:
    # An HTML response is treated as an error (often a proxy in between SOAR and WiGLE)
    try:
        soup = BeautifulSoup(response.text, "html.parser")
        # Remove the script, style, footer and navigation part from the HTML message
        for element in soup(["script", "style", "footer", "nav"]):
            element.extract()
        split_lines = [line.strip() for line in soup.text.split("\n") if line.strip()]
        error_text = "\n".join(split_lines)
    except Exception:
        error_text = "Cannot parse error details"

    raise ActionFailure(
        f"Status Code: {response.status_code}. Data from server:\n{error_text}\n"
    )


def _process_json_response(response: requests.Response) -> dict[str, Any]:
    if response.status_code >= 400:
        raise ActionFailure(
            f"Error from server. Status Code: {response.status_code} Data from server: {response.text}"
        )

    try:
        resp_json = response.json()
    except Exception as e:
        raise ActionFailure(f"Unable to parse JSON response. Error: {e!s}") from e

    if not isinstance(resp_json, dict):
        raise ActionFailure(
            f"Unexpected JSON response from server: expected an object, got {type(resp_json).__name__}"
        )

    if not resp_json.get("success", True):
        raise ActionFailure(
            f"Server returned Failure. Message: {resp_json.get('message', 'None')}"
        )

    if 200 <= response.status_code < 399:
        return resp_json

    raise ActionFailure(
        f"Error from server. Status Code: {response.status_code} Data from server: {response.text}"
    )


def process_response(response: requests.Response) -> dict[str, Any]:
    """Convert a WiGLE HTTP response to a JSON dict, raising ActionFailure on any error."""
    content_type = response.headers.get("Content-Type", "")

    if "json" in content_type:
        return _process_json_response(response)

    if "html" in content_type:
        return _process_html_response(response)

    if not response.text:
        return _process_empty_response(response)

    raise ActionFailure(
        f"Can't process response from server. Status Code: {response.status_code} Data from server: {response.text}"
    )


def make_rest_call(
    api_name: str, api_token: str, endpoint: str, params: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Make an authenticated GET request to the WiGLE v2 API and return the parsed JSON body."""
    url = f"{WIGLE_BASE_URL}{endpoint}"
    try:
        response = requests.get(
            url,
            auth=(api_name, api_token),  # basic authentication
            params=params,
            timeout=DEFAULT_REQUEST_TIMEOUT,
        )
    except Exception as e:
        raise ActionFailure(f"Error Connecting to server. Details: {e!s}") from e

    return process_response(response)
