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
import uuid

import requests
from bs4 import BeautifulSoup
from pydantic import ConfigDict, field_validator
from soar_sdk.abstract import SOARClient
from soar_sdk.action_results import ActionOutput, ActionResult, OutputField
from soar_sdk.app import App
from soar_sdk.asset import AssetField, BaseAsset
from soar_sdk.exceptions import ActionFailure
from soar_sdk.logging import info
from soar_sdk.params import Param, Params


MAX_COMMERCIAL_PAGE_SIZE = 1000


class Asset(BaseAsset):
    api_name: str = AssetField(description="API Name")
    api_token: str = AssetField(description="API Token", sensitive=True)


app = App(
    name="WiGLE",
    app_type="information",
    logo="logo_wigle.svg",
    logo_dark="logo_wigle_dark.svg",
    product_vendor="WiGLE",
    product_name="WiGLE",
    publisher="Splunk",
    appid="41a0b155-215c-435f-987a-a14c3a1b698f",
    fips_compliant=True,
    asset_cls=Asset,
)


def search_network(asset: Asset, params: dict) -> dict:
    try:
        response = requests.get(
            "https://api.wigle.net/api/v2/network/search",
            auth=(asset.api_name, asset.api_token),
            params=params,
            timeout=30,
        )
    except requests.RequestException as exc:
        raise ActionFailure(f"Error Connecting to server. Details: {exc!s}") from exc

    content_type = response.headers.get("Content-Type", "")
    if "json" in content_type:
        if response.status_code >= 400:
            raise ActionFailure(
                f"Error from server. Status Code: {response.status_code} Data from server: {response.text}"
            )
        try:
            data = response.json()
        except ValueError as exc:
            raise ActionFailure(
                f"Unable to parse JSON response. Error: {exc!s}"
            ) from exc
        if not isinstance(data, dict):
            raise ActionFailure(
                f"Unexpected JSON response from server: expected an object, got {type(data).__name__}"
            )
        if not data.get("success", True):
            raise ActionFailure(
                f"Server returned Failure. Message: {data.get('message', 'None')}"
            )
        if 200 <= response.status_code < 399:
            return data
        raise ActionFailure(
            f"Error from server. Status Code: {response.status_code} Data from server: {response.text}"
        )
    if "html" in content_type:
        try:
            soup = BeautifulSoup(response.text, "html.parser")
            for element in soup(["script", "style", "footer", "nav"]):
                element.extract()
            error_text = "\n".join(
                line.strip() for line in soup.text.split("\n") if line.strip()
            )
        except Exception:
            error_text = "Cannot parse error details"
        raise ActionFailure(
            f"Status Code: {response.status_code}. Data from server:\n{error_text}\n"
        )
    if not response.text:
        if response.status_code == 200:
            return {}
        raise ActionFailure("Empty response and no information in the header")
    raise ActionFailure(
        f"Can't process response from server. Status Code: {response.status_code} Data from server: {response.text}"
    )


@app.test_connectivity()
def test_connectivity(soar: SOARClient, asset: Asset) -> None:
    ssid = str(uuid.uuid4())[:8]
    # The SDK writes info-level progress to persistent SOAR action history.
    info(f"Querying a randomly generated SSID name: {ssid} to test connectivity")
    try:
        search_network(asset, {"ssid": ssid, "resultsPerPage": 1})
    except ActionFailure:
        info("Test Connectivity Failed")
        raise
    info("Test Connectivity Passed")


class LookupNetworkParams(Params):
    name: str = Param(description="SSID", primary=True, cef_types=["ssid"])
    max_results: int = Param(
        description="Max results per page (default 100, maximum 100 for standard API and 1000 for COMMAPI)",
        default=100,
        required=False,
    )
    page_token: str | None = Param(
        description="Page Token (Should be empty to get the 1st page)",
        primary=True,
        cef_types=["page token"],
        default=None,
    )

    @field_validator("page_token", mode="before")
    @classmethod
    def accept_legacy_numeric_cursor(cls, value: object) -> object:
        if isinstance(value, int) and not isinstance(value, bool):
            return str(value)
        return value


class VendorOutput(ActionOutput):
    def model_dump(self, **kwargs):
        # The legacy app omits absent vendor fields rather than adding nulls.
        kwargs.setdefault("exclude_unset", True)
        return super().model_dump(**kwargs)


class LookupNetworkOutput(VendorOutput):
    model_config = ConfigDict(extra="allow")

    ssid: str = OutputField(
        cef_types=["ssid"], example_values=["foobar"], column_name="Ssid"
    )
    encryption: str = OutputField(example_values=["wpa2"], column_name="Encryption")
    city: str = OutputField(column_name="City")
    region: str = OutputField(
        example_values=["u041cu043eu0441u043au0432u0430"], column_name="Region"
    )
    country: str = OutputField(example_values=["RU"], column_name="Country")
    bcninterval: float = OutputField(example_values=[0])
    channel: float = OutputField(example_values=[1])
    comment: str
    dhcp: str = OutputField(example_values=["?"])
    firsttime: str = OutputField(example_values=["2013-12-13T11:00:00.000Z"])
    freenet: str = OutputField(example_values=["?"])
    housenumber: str
    postalcode: str = OutputField(example_values=["78758"])
    lasttime: str = OutputField(example_values=["2013-12-13T01:00:00.000Z"])
    lastupdt: str = OutputField(example_values=["2013-12-12T23:00:00.000Z"])
    name: str
    netid: str = OutputField(example_values=["14:DA:E9:80:F0:8C"])
    paynet: str = OutputField(example_values=["?"])
    qos: float = OutputField(example_values=[0])
    road: str
    transid: str = OutputField(example_values=["20131213-00000"])
    trilat: float = OutputField(example_values=[55.728405])
    trilong: float = OutputField(example_values=[37.41586685])
    type: str = OutputField(example_values=["infra"])
    userfound: bool = OutputField(example_values=[True, False])
    wep: str = OutputField(example_values=["2"])


class LookupNetworkSummary(VendorOutput):
    first: float = OutputField(example_values=[1])
    last: float = OutputField(example_values=[5])
    next_page_token: str | None = OutputField(
        cef_types=["page token"], example_values=["85872166"]
    )
    result_count: float = OutputField(example_values=[5])
    total_results: float = OutputField(example_values=[5])


def failed_lookup(params: LookupNetworkParams, message: str) -> ActionResult:
    result = ActionResult(False, message, param=params.model_dump(exclude_none=True))
    result.set_summary({"total_results": 0})
    return result


@app.action(
    name="lookup network",
    identifier="lookup_network",
    description="Get info about a WiFi SSID",
    action_type="investigate",
    read_only=True,
    render_as="table",
    summary_type=LookupNetworkSummary,
    output_class=LookupNetworkOutput,
)
def lookup_network(params: LookupNetworkParams, soar: SOARClient, asset: Asset):
    if not 1 <= params.max_results <= MAX_COMMERCIAL_PAGE_SIZE:
        return failed_lookup(
            params, f"max_results must be between 1 and {MAX_COMMERCIAL_PAGE_SIZE}"
        )

    query = {"ssid": params.name, "resultsPerPage": params.max_results}
    if params.page_token is not None:
        query["searchAfter"] = params.page_token
    try:
        response = search_network(asset, query)
    except ActionFailure as exc:
        return failed_lookup(params, exc.message)

    results = response.get("results", [])
    if not isinstance(results, list) or any(
        not isinstance(item, dict) for item in results
    ):
        return failed_lookup(
            params, "Invalid WiGLE response: results must be an array of objects"
        )

    summary = {"total_results": response.get("totalResults", 0)}
    cursor = response.get("searchAfter")
    if cursor is None:
        cursor = response.get("search_after")
    if cursor is not None:
        summary["next_page_token"] = str(cursor)
    for source, target in [
        ("first", "first"),
        ("last", "last"),
        ("resultCount", "result_count"),
    ]:
        if source in response:
            summary[target] = response[source]
    soar.set_summary(LookupNetworkSummary.model_construct(**summary))
    soar.set_message(
        ", ".join(
            f"{key.replace('_', ' ').capitalize()}: {value}"
            for key, value in summary.items()
        )
    )
    return [LookupNetworkOutput.model_construct(**item) for item in results]


if __name__ == "__main__":
    app.cli()
