"""chargebacks tap class."""

from typing import List

from singer_sdk import Tap, Stream
from singer_sdk import typing as th  # JSON schema typing helpers


from tap_chargebacks.streams import (
    ChargebacksStream,
    AlertsStream,
)

STREAM_TYPES = [
    AlertsStream,
    ChargebacksStream,
]

class Tapchargebacks(Tap):
    """chargebacks tap class."""
    name = "tap-chargebacks"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "user",
            th.StringType,
            required=True,
            description="The user for the Chargebacks API."
        ),
        th.Property(
            "password",
            th.StringType,
            required=True,
            description="The password for the Chargebacks API."
        ),
        th.Property(
            "start_date",
            th.DateTimeType,
            description="The earliest record date to sync"
        ),
        th.Property(
            "merchant_id",
            th.StringType,
            required=True,
            description="The merchant ID to use for alert and chargeback calls."
        ),
    ).to_dict()

    def discover_streams(self) -> List[Stream]:
        """Return a list of discovered streams."""
        return [stream_class(tap=self) for stream_class in STREAM_TYPES]
