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
import uuid

from pydantic import ConfigDict
from soar_sdk.abstract import SOARClient
from soar_sdk.action_results import ActionOutput, OutputField
from soar_sdk.app import App
from soar_sdk.asset import AssetField, BaseAsset, FieldCategory
from soar_sdk.exceptions import ActionFailure
from soar_sdk.logging import getLogger
from soar_sdk.params import Param, Params

from .consts import DEFAULT_MAX_RESULTS, WIGLE_NETWORK_SEARCH_ENDPOINT
from .helper import make_rest_call


logger = getLogger()


class Asset(BaseAsset):
    api_name: str = AssetField(
        required=True,
        description="API Name",
        category=FieldCategory.CONNECTIVITY,
    )
    api_token: str = AssetField(
        required=True,
        description="API Token",
        sensitive=True,
        category=FieldCategory.CONNECTIVITY,
    )


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


@app.test_connectivity()
def test_connectivity(soar: SOARClient, asset: Asset) -> None:
    """Validate the asset configuration for connectivity."""
    ssid = str(uuid.uuid4())[:8]
    logger.info(f"Querying a randomly generated SSID name: {ssid} to test connectivity")

    try:
        make_rest_call(
            asset.api_name,
            asset.api_token,
            WIGLE_NETWORK_SEARCH_ENDPOINT,
            params={"ssid": ssid, "resultsPerPage": 1},
        )
    except ActionFailure:
        logger.info("Test Connectivity Failed")
        raise

    logger.info("Test Connectivity Passed")


class LookupNetworkParams(Params):
    name: str = Param(
        description="SSID", required=True, primary=True, cef_types=["ssid"]
    )
    max_results: int | None = Param(
        description="Max results per page (default is 100)",
        default=DEFAULT_MAX_RESULTS,
    )
    page_token: str | None = Param(
        description="Page Token (Should be empty to get the 1st page)",
        primary=True,
        cef_types=["page token"],
    )


class LookupNetworkOutput(ActionOutput):
    # WiGLE may return numbers for string fields (e.g. postal codes); keep them as strings.
    # extra="allow" keeps every key WiGLE returns in action_result.data, as the legacy app did.
    model_config = ConfigDict(coerce_numbers_to_str=True, extra="allow")

    # Table columns, declared in the original manifest's column order.
    ssid: str | None = OutputField(
        column_name="Ssid", cef_types=["ssid"], example_values=["foobar"]
    )
    encryption: str | None = OutputField(
        column_name="Encryption", example_values=["wpa2"]
    )
    city: str | None = OutputField(column_name="City")
    region: str | None = OutputField(
        column_name="Region", example_values=["u041cu043eu0441u043au0432u0430"]
    )
    country: str | None = OutputField(column_name="Country", example_values=["RU"])

    bcninterval: int | None = OutputField(example_values=[0])
    channel: int | None = OutputField(example_values=[1])
    comment: str | None = None
    dhcp: str | None = OutputField(example_values=["?"])
    firsttime: str | None = OutputField(example_values=["2013-12-13T11:00:00.000Z"])
    freenet: str | None = OutputField(example_values=["?"])
    housenumber: str | None = None
    postalcode: str | None = OutputField(example_values=["78758"])
    lasttime: str | None = OutputField(example_values=["2013-12-13T01:00:00.000Z"])
    lastupdt: str | None = OutputField(example_values=["2013-12-12T23:00:00.000Z"])
    name: str | None = None
    netid: str | None = OutputField(example_values=["14:DA:E9:80:F0:8C"])
    paynet: str | None = OutputField(example_values=["?"])
    qos: int | None = OutputField(example_values=[0])
    road: str | None = None
    transid: str | None = OutputField(example_values=["20131213-00000"])
    trilat: float | None = OutputField(example_values=[55.728405])
    trilong: float | None = OutputField(example_values=[37.41586685])
    type: str | None = OutputField(example_values=["infra"])
    userfound: bool | None = OutputField(example_values=[True, False])
    wep: str | None = OutputField(example_values=["2"])


class LookupNetworkSummary(ActionOutput):
    model_config = ConfigDict(coerce_numbers_to_str=True)

    total_results: int = OutputField(example_values=[5])
    next_page_token: str | None = OutputField(
        cef_types=["page token"], example_values=["85872166"]
    )
    first: int | None = OutputField(example_values=[1])
    last: int | None = OutputField(example_values=[5])
    result_count: int | None = OutputField(example_values=[5])


def _summary_message(summary: LookupNetworkSummary) -> str:
    labels = {
        "total_results": "Total results",
        "next_page_token": "Next page token",
        "result_count": "Result count",
        "last": "Last",
        "first": "First",
    }
    values = summary.model_dump()
    return ", ".join(
        f"{label}: {values[key]}"
        for key, label in labels.items()
        if values.get(key) is not None
    )


@app.action(
    description="Get info about a WiFi SSID",
    action_type="investigate",
    read_only=True,
    render_as="table",
    summary_type=LookupNetworkSummary,
)
def lookup_network(
    params: LookupNetworkParams, soar: SOARClient, asset: Asset
) -> list[LookupNetworkOutput]:
    """Get info about a WiFi SSID."""
    max_results = (
        params.max_results if params.max_results is not None else DEFAULT_MAX_RESULTS
    )
    if max_results <= 0:
        raise ActionFailure("'max_results' action parameter must be a positive integer")

    query = {"ssid": params.name, "resultsPerPage": max_results}
    if params.page_token:
        query["searchAfter"] = params.page_token

    logger.debug("Making rest call for lookup network")
    response = make_rest_call(
        asset.api_name, asset.api_token, WIGLE_NETWORK_SEARCH_ENDPOINT, params=query
    )

    summary = LookupNetworkSummary(
        total_results=response.get("totalResults") or 0,
        next_page_token=response.get("search_after"),
        first=response.get("first"),
        last=response.get("last"),
        result_count=response.get("resultCount"),
    )
    soar.set_summary(summary)
    soar.set_message(_summary_message(summary))

    results = response.get("results") or []
    return [LookupNetworkOutput(**item) for item in results if isinstance(item, dict)]


if __name__ == "__main__":
    app.cli()
