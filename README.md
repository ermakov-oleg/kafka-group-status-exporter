# Kafka consumer group status exporter

This exporter exports all the statuses of the consumer group and all their active members 

Exported metrics are:
* `kafka_consumer_group_status` - status of the consumer group (UNKOWN/PREPARING_REBALANCING/COMPLETING_REBALANCING/STABLE/DEAD/EMPTY)
* `kafka_consumer_group_member` - all active members of the consumer group with their client_id and host.

## Usage

```bash
kafka-group-status-exporter --config example.json
```

## Connection configuration
Connection configuration is done via a JSON file.
All parameters pass as is to the [librdkafka consumer](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md)


## Extract client_id for consumer group members

Example:

Real client_id is `some-kafka-consumer[some-instance-info]` and you want to extract `some-kafka-consumer`:

```bash
kafka-consumer-groups --client-id-extract-regex '(?P<client_id>[\w-]*)'
```

Regex should contain a named group `client_id` that will be used as a client_id for the consumer group member.
