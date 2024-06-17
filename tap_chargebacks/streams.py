"""Stream type classes for tap-chargebacks."""

from pathlib import Path
from typing import Any, Dict, Optional, Union, List, Iterable
import typing as t

from singer_sdk import typing as th  # JSON Schema typing helpers
from singer_sdk import metrics

from memoization import cached
import requests

from singer_sdk.helpers.jsonpath import extract_jsonpath
from singer_sdk.streams import RESTStream


SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")

class ChargebacksStream(RESTStream):
    """Define custom stream."""
    name = "chargebacks"
    path = f"/clients/FIXD_Automotive_Inc/chargebacks"
    primary_keys = ["id"]
    replication_key = None
    url_base = "https://api.cbresponseservices.com/v2"
    schema_filepath = SCHEMAS_DIR / "chargebacks.json"

    records_jsonpath = "$[data][*]"

    @property
    def http_headers(self) -> dict:
        """Return the http headers needed."""
        auth_url = "https://api.cbresponseservices.com/v2/auth"
        response = requests.get(auth_url, auth = (self.config.get("user"), self.config.get("password")))
        access_token = response.json()["data"]["accessToken"]
        headers = {}
        headers["Authorization"] = f"Bearer {access_token}"
        if "user_agent" in self.config:
            headers["User-Agent"] = self.config.get("user_agent")
        return headers

    def get_url_params(
        self, context: Optional[dict], next_page_token: Optional[Any]
    ) -> Dict[str, Any]:
        """Return a dictionary of values to be used in URL parameterization."""
        params: dict = {}
        params["limit"] = "2500"
        if next_page_token:
            params["page"] = next_page_token
        params["start_date"] = self.config.get("start_date")
        if self.replication_key:
            params["sort"] = "asc"
            params["order_by"] = self.replication_key
        return params
    
    def request_records(self, context: Optional[Any]) -> t.Iterable[dict]:
        """Request records from REST endpoint(s), returning response records.

        If pagination is detected, pages will be recursed automatically.

        Args:
            context: Stream partition or context dictionary.

        Yields:
            An item for every record in the response.
        """
        decorated_request = self.request_decorator(self._request)
        page = 1

        with metrics.http_request_counter(self.name, self.path) as request_counter:
            request_counter.context = context
            while True:
                prepared_request = self.prepare_request(
                    context,
                    next_page_token=page
                )
                resp = decorated_request(prepared_request, context)
                request_counter.increment()
                self.update_sync_costs(prepared_request, resp, context)
                records = iter(self.parse_response(resp))
                try:
                    first_record = next(records)
                except StopIteration:
                    self.logger.info(
                        "Pagination stopped after %d pages because no records were "
                        "found in the last response",
                        page,
                    )
                    break
                yield first_record
                yield from records
                page += 1
                if len(resp.json()['data']) == 0:
                    break


class AlertsStream(RESTStream):
    """Define custom stream."""
    name = "alerts"
    path = f"/clients/FIXD_Automotive_Inc/alerts"
    primary_keys = ["id"]
    replication_key = None
    url_base = "https://api.cbresponseservices.com/v2"
    schema_filepath = SCHEMAS_DIR / "alerts.json"

    records_jsonpath = "$[data][*]"

    @property
    def http_headers(self) -> dict:
        """Return the http headers needed."""
        auth_url = "https://api.cbresponseservices.com/v2/auth"
        response = requests.get(auth_url, auth = (self.config.get("user"), self.config.get("password")))
        access_token = response.json()["data"]["accessToken"]
        headers = {}
        headers["Authorization"] = f"Bearer {access_token}"
        if "user_agent" in self.config:
            headers["User-Agent"] = self.config.get("user_agent")
        return headers

    def get_next_page_token(
        self, response: requests.Response, previous_token: Optional[Any]
    ) -> Optional[Any]:
        """Return a token for identifying next page or None if no more pages."""
        total_pages = response.json()['pagination']['total_pages']
        current_page = response.json()['pagination']['current_page']
        while current_page <= total_pages:
            next_page_token = current_page + 1
            return next_page_token

    def get_url_params(
        self, context: Optional[dict], next_page_token: Optional[Any]
    ) -> Dict[str, Any]:
        """Return a dictionary of values to be used in URL parameterization."""
        params: dict = {}
        if next_page_token:
            params["page"] = next_page_token
        if self.replication_key:
            params["sort"] = "asc"
            params["order_by"] = self.replication_key
        return params