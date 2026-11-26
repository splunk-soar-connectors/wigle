# Copyright (c) 2026 Splunk Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import json
from unittest.mock import Mock

import pytest
import requests
from soar_sdk.exceptions import ActionFailure

from src import app as module


@pytest.fixture
def asset():
    return module.Asset(api_name="example-name", api_token="example-token")


@pytest.fixture
def request_mock(monkeypatch):
    request = Mock()
    monkeypatch.setattr(module.requests, "get", request)
    return request


def response(body, status=200, content_type="application/json"):
    result = requests.Response()
    result.status_code = status
    result.headers["Content-Type"] = content_type
    result._content = (
        json.dumps(body) if content_type == "application/json" else body
    ).encode()
    return result


def test_lookup_page_and_summary(asset, request_mock):
    row = {"ssid": "Example", "netid": "00:11:22:33:44:55", "vendor_extra": [1]}
    request_mock.return_value = response(
        {
            "success": True,
            "results": [row],
            "totalResults": 5,
            "search_after": 123,
            "first": 1,
            "last": 1,
            "resultCount": 1,
        }
    )
    soar = Mock()
    output = module.lookup_network.__wrapped__(
        module.LookupNetworkParams(name="Example", page_token="previous"), soar, asset
    )
    request_mock.assert_called_once_with(
        "https://api.wigle.net/api/v2/network/search",
        auth=("example-name", "example-token"),
        params={"ssid": "Example", "resultsPerPage": 100, "searchAfter": "previous"},
        timeout=30,
    )
    assert [item.model_dump() for item in output] == [row]
    assert soar.set_summary.call_args.args[0].model_dump() == {
        "total_results": 5,
        "next_page_token": 123,
        "first": 1,
        "last": 1,
        "result_count": 1,
    }


def test_first_page_empty_result(asset, request_mock):
    request_mock.return_value = response({"success": True})
    soar = Mock()
    assert (
        module.lookup_network.__wrapped__(
            module.LookupNetworkParams(name="Example", max_results=25), soar, asset
        )
        == []
    )
    assert request_mock.call_args.kwargs["params"] == {
        "ssid": "Example",
        "resultsPerPage": 25,
    }
    assert soar.set_summary.call_args.args[0].model_dump() == {"total_results": 0}


def test_connectivity_random_query(asset, request_mock, monkeypatch):
    monkeypatch.setattr(module, "progress", Mock())
    request_mock.return_value = response({"success": True})
    module.test_connectivity.__wrapped__(Mock(), asset)
    query = request_mock.call_args.kwargs["params"]
    assert query["resultsPerPage"] == 1
    assert len(query["ssid"]) == 8


@pytest.mark.parametrize(
    "body,status,content_type,error",
    [
        (
            {"success": False, "message": "denied"},
            200,
            "application/json",
            "Server returned Failure",
        ),
        ({"message": "bad credentials"}, 401, "application/json", "Status Code: 401"),
        ([], 200, "application/json", "expected an object"),
        ("invalid", 200, "application/json-broken", "Unable to parse JSON"),
        (
            "<html><script>hidden</script><p>Denied</p></html>",
            403,
            "text/html",
            "Denied",
        ),
        ("", 204, "text/plain", "Empty response"),
        ("oops", 500, "text/plain", "Can't process response"),
    ],
)
def test_response_failures(asset, request_mock, body, status, content_type, error):
    request_mock.return_value = response(body, status, content_type)
    with pytest.raises(ActionFailure, match=error):
        module.search_network(asset, {})


def test_invalid_json(asset, request_mock):
    request_mock.return_value = response("not json", 200, "text/plain")
    request_mock.return_value.headers["Content-Type"] = "application/json"
    with pytest.raises(ActionFailure, match="Unable to parse JSON"):
        module.search_network(asset, {})


def test_empty_ok(asset, request_mock):
    request_mock.return_value = response("", 200, "text/plain")
    assert module.search_network(asset, {}) == {}


def test_transport_failure(asset, request_mock):
    request_mock.side_effect = requests.Timeout("timed out")
    with pytest.raises(ActionFailure, match="Error Connecting to server"):
        module.search_network(asset, {})


def test_sdk_decorated_lookup(asset, request_mock, monkeypatch):
    monkeypatch.setattr(module.app, "_asset", asset, raising=False)
    request_mock.return_value = response(
        {"results": [{"ssid": "Example"}], "resultCount": 1}
    )
    assert module.lookup_network(module.LookupNetworkParams(name="Example")) is True
    result = module.app.actions_manager.get_results()[-1]
    assert result.get_data() == [{"ssid": "Example"}]
    assert result.get_summary() == {"total_results": 0, "result_count": 1}


def test_sdk_decorated_connectivity_failure(asset, request_mock, monkeypatch):
    monkeypatch.setattr(module.app, "_asset", asset, raising=False)
    request_mock.return_value = response({"success": False, "message": "denied"})
    assert module.test_connectivity({}) is False
    assert "denied" in module.app.actions_manager.get_results()[-1].get_message()


def test_sdk_decorated_connectivity_success(asset, request_mock, monkeypatch):
    monkeypatch.setattr(module.app, "_asset", asset, raising=False)
    request_mock.return_value = response({"success": True})
    assert module.test_connectivity({}) is True


def test_output_preserves_explicit_null_and_extra_fields():
    output = module.LookupNetworkOutput.model_construct(ssid=None, vendor_field="value")
    assert output.model_dump() == {"ssid": None, "vendor_field": "value"}


@pytest.mark.parametrize("maximum", [1, 25, 100])
def test_explicit_page_size_uses_integer_wire_value(asset, request_mock, maximum):
    request_mock.return_value = response({"results": []})
    module.lookup_network.__wrapped__(
        module.LookupNetworkParams(name="Example", max_results=maximum), Mock(), asset
    )
    query = request_mock.call_args.kwargs["params"]
    prepared = requests.Request(
        "GET", request_mock.call_args.args[0], params=query
    ).prepare()
    assert prepared.url.endswith(f"resultsPerPage={maximum}")
    assert isinstance(query["resultsPerPage"], int)


def test_sdk_failed_lookup_keeps_legacy_summary(asset, request_mock, monkeypatch):
    monkeypatch.setattr(module.app, "_asset", asset, raising=False)
    request_mock.return_value = response({"success": False, "message": "denied"})
    assert module.lookup_network(module.LookupNetworkParams(name="Example")) is False
    result = module.app.actions_manager.get_results()[-1]
    assert result.get_summary() == {"total_results": 0}
    assert result.get_param() == {"name": "Example", "max_results": 100}
    assert result.get_message() == "Server returned Failure. Message: denied"
