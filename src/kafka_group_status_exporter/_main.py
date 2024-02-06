import logging
import re
from dataclasses import dataclass
from time import sleep
from typing import Any

from confluent_kafka.admin import AdminClient
from prometheus_client import Gauge

logger = logging.getLogger(__name__)


kafka_consumer_group_status = Gauge(
    'kafka_consumer_group_status',
    'Kafka consumer group status',
    ['group_id', 'state']
)

kafka_consumer_group_member = Gauge(
    'kafka_consumer_group_member',
    'Kafka consumer group member',
    ['group_id', 'client_id', 'host']
)


def collect(config: dict[str, Any], interval: float, client_id_extract_regex: str) -> None:
    client_id_extract_re = re.compile(client_id_extract_regex)
    client = AdminClient(config)
    while True:
        collect_once(client, client_id_extract_re)
        sleep(interval)


def collect_once(client: AdminClient, client_id_extract_re: re.Pattern) -> None:
    status = _get_consumer_groups_status(client)

    # Clear all previous metrics
    kafka_consumer_group_status.clear()
    kafka_consumer_group_member.clear()

    for group_id, group_status in status.items():
        kafka_consumer_group_status.labels(group_id=group_id, state=group_status.state).set(1)
        for member in group_status.members:
            if match := client_id_extract_re.match(member.client_id):
                client_id = match.group('client_id')
                kafka_consumer_group_member.labels(
                    group_id=group_id,
                    client_id=client_id,
                    host=member.host
                ).set(1)


@dataclass
class _GroupMember:
    client_id: str
    host: str


@dataclass
class _ConsumerGroupStatus:
    group_id: str
    state: str
    members: list[_GroupMember]


def _get_consumer_groups_status(client: AdminClient) -> dict[str, _ConsumerGroupStatus]:
    consumer_groups_response = client.list_consumer_groups().result()
    if consumer_groups_response.errors:
        logger.error('Failed to list consumer groups: %s', consumer_groups_response.errors)

    if not consumer_groups_response.valid:
        return {}

    consumer_groups = [val.group_id for val in consumer_groups_response.valid]

    describe_groups_response = client.describe_consumer_groups(consumer_groups)
    consumer_groups_status = {}
    for group_id, group_info_fut in describe_groups_response.items():
        group_info = group_info_fut.result()
        consumer_groups_status[group_id] = _ConsumerGroupStatus(
            group_id=group_id,
            state=group_info.state.name,
            members=[
                _GroupMember(
                    client_id=member.client_id,
                    host=member.host
                )
                for member in group_info.members
            ]
        )
    return consumer_groups_status
