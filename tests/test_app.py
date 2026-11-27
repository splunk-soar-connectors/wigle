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
from unittest.mock import MagicMock

import pytest
import requests
from soar_sdk.exceptions import ActionFailure

from src import app as wigle_app, helper


def _response(
    status_code=200, content_type="application/json", json_body=None, text=None
):
    response = MagicMock(spec=requests.Response)
    response.status_code = status_code
    response.headers = {"Content-Type": content_type} if content_type else {}
    response.text = (
        text if text is not None else ("{}" if json_body is None else str(json_body))
    )
    if isinstance(json_body, Exception):
        response.json.side_effect = json_body
    else:
        response.json.return_value = json_body
    return response


@pytest.fixture
def asset():
    return wigle_app.Asset(api_name="name", api_token="token")


@pytest.fixture
def soar():
    return MagicMock()


def test_process_json_success():
    assert helper.process_response(_response(json_body={"success": True, "a": 1})) == {
        "success": True,
        "a": 1,
    }


@pytest.mark.parametrize(
    ("response", "match"),
    [
        (
            _response(
                status_code=401, json_body={"success": False}, text="unauthorized"
            ),
            "Status Code: 401",
        ),
        (_response(json_body=ValueError("bad")), "Unable to parse JSON response"),
        (_response(json_body=[1, 2]), "expected an object, got list"),
        (
            _response(json_body={"success": False, "message": "too many queries"}),
            "Server returned Failure. Message: too many queries",
        ),
        (
            _response(
                content_type="text/html",
                text="<html><script>x</script><p>Bad gateway</p></html>",
                status_code=502,
            ),
            "Bad gateway",
        ),
        (
            _response(content_type="text/plain", text="oops", status_code=500),
            "Can't process response",
        ),
        (_response(status_code=500, content_type=None, text=""), "Empty response"),
    ],
)
def test_process_response_errors(response, match):
    with pytest.raises(ActionFailure, match=match):
        helper.process_response(response)


def test_process_empty_200():
    assert helper.process_response(_response(content_type=None, text="")) == {}


def test_make_rest_call_uses_basic_auth_and_timeout(mocker):
    get = mocker.patch.object(
        helper.requests, "get", return_value=_response(json_body={"success": True})
    )
    helper.make_rest_call("user", "secret", "/network/search", params={"ssid": "x"})
    get.assert_called_once_with(
        "https://api.wigle.net/api/v2/network/search",
        auth=("user", "secret"),
        params={"ssid": "x"},
        timeout=30,
    )


def test_make_rest_call_connection_error(mocker):
    mocker.patch.object(
        helper.requests, "get", side_effect=requests.ConnectionError("boom")
    )
    with pytest.raises(
        ActionFailure, match=r"Error Connecting to server\. Details: boom"
    ):
        helper.make_rest_call("user", "secret", "/network/search")


def test_test_connectivity_success(mocker, soar, asset):
    call = mocker.patch.object(
        wigle_app, "make_rest_call", return_value={"success": True}
    )
    wigle_app.test_connectivity.__wrapped__(soar, asset)
    _, _, endpoint = call.call_args.args
    assert endpoint == "/network/search"
    assert call.call_args.kwargs["params"]["resultsPerPage"] == 1


def test_test_connectivity_failure(mocker, soar, asset):
    mocker.patch.object(wigle_app, "make_rest_call", side_effect=ActionFailure("nope"))
    with pytest.raises(ActionFailure, match="nope"):
        wigle_app.test_connectivity.__wrapped__(soar, asset)


def test_lookup_network(mocker, soar, asset):
    call = mocker.patch.object(
        wigle_app,
        "make_rest_call",
        return_value={
            "success": True,
            "totalResults": 2,
            "first": 1,
            "last": 2,
            "resultCount": 2,
            "search_after": 85872166,
            "results": [
                {
                    "ssid": "foobar",
                    "encryption": "wpa2",
                    "postalcode": 78758,
                    "trilat": 1.5,
                    "userfound": False,
                    "extra": {"x": 1},
                },
                {"ssid": "foobar", "city": None},
            ],
        },
    )
    params = wigle_app.LookupNetworkParams(
        name="foobar", max_results=10, page_token="abc"
    )

    results = wigle_app.lookup_network.__wrapped__(params, soar=soar, asset=asset)

    assert call.call_args.kwargs["params"] == {
        "ssid": "foobar",
        "resultsPerPage": 10,
        "searchAfter": "abc",
    }
    assert len(results) == 2
    assert results[0].postalcode == "78758"
    assert results[0].encryption == "wpa2"
    summary = soar.set_summary.call_args.args[0]
    assert summary.total_results == 2
    assert summary.next_page_token == "85872166"
    soar.set_message.assert_called_once_with(
        "Total results: 2, Next page token: 85872166, Result count: 2, Last: 2, First: 1"
    )


def test_lookup_network_defaults_and_no_page_token(mocker, soar, asset):
    call = mocker.patch.object(
        wigle_app, "make_rest_call", return_value={"success": True}
    )
    params = wigle_app.LookupNetworkParams(name="foobar")

    results = wigle_app.lookup_network.__wrapped__(params, soar=soar, asset=asset)

    assert results == []
    assert call.call_args.kwargs["params"] == {"ssid": "foobar", "resultsPerPage": 100}
    soar.set_message.assert_called_once_with("Total results: 0")


@pytest.mark.parametrize("value", [0, -5])
def test_lookup_network_invalid_max_results(mocker, soar, asset, value):
    call = mocker.patch.object(wigle_app, "make_rest_call")
    params = wigle_app.LookupNetworkParams(name="foobar", max_results=value)
    with pytest.raises(ActionFailure, match="positive integer"):
        wigle_app.lookup_network.__wrapped__(params, soar=soar, asset=asset)
    call.assert_not_called()


def test_lookup_network_through_sdk_wrapper(mocker, asset):
    """Run the registered action through the SDK wrapper to check result adaptation."""
    mocker.patch.object(
        wigle_app,
        "make_rest_call",
        return_value={
            "success": True,
            "totalResults": 1,
            "results": [{"ssid": "foobar", "channel": 6}],
        },
    )
    actions_manager = wigle_app.app.actions_manager
    mocker.patch.object(
        wigle_app.app,
        "_build_magic_args",
        side_effect=lambda fn, soar, **kw: {"soar": soar, "asset": asset},
    )
    added = mocker.patch.object(actions_manager, "add_result")

    status = wigle_app.lookup_network(wigle_app.LookupNetworkParams(name="foobar"))

    assert status is True
    result = added.call_args.args[0]
    assert result.get_data()[0]["ssid"] == "foobar"
    assert result.get_data()[0]["channel"] == 6
    assert result.get_summary()["total_results"] == 1
