import time

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from src.dependencies.local_chat_seed import seed_local_chats
from src.dependencies.settings import ChatInfrastructureMode, get_settings


def main() -> None:
    settings = get_settings()
    if settings.chat_infrastructure_mode is not ChatInfrastructureMode.LOCAL:
        raise ValueError("Local DynamoDB initialization requires local mode")
    assert settings.dynamodb_endpoint_url is not None
    client = boto3.client(
        "dynamodb",
        region_name=settings.aws_region,
        endpoint_url=settings.dynamodb_endpoint_url,
    )

    for attempt in range(30):
        try:
            client.create_table(
                TableName=settings.dynamodb_chat_table_name,
                AttributeDefinitions=[
                    {"AttributeName": "pk", "AttributeType": "S"},
                    {"AttributeName": "sk", "AttributeType": "S"},
                    {"AttributeName": "gsi1pk", "AttributeType": "S"},
                    {"AttributeName": "gsi1sk", "AttributeType": "S"},
                ],
                KeySchema=[
                    {"AttributeName": "pk", "KeyType": "HASH"},
                    {"AttributeName": "sk", "KeyType": "RANGE"},
                ],
                GlobalSecondaryIndexes=[
                    {
                        "IndexName": "gsi1",
                        "KeySchema": [
                            {"AttributeName": "gsi1pk", "KeyType": "HASH"},
                            {"AttributeName": "gsi1sk", "KeyType": "RANGE"},
                        ],
                        "Projection": {
                            "ProjectionType": "INCLUDE",
                            "NonKeyAttributes": [
                                "chat_id",
                                "title",
                                "created_at",
                                "last_updated_at",
                            ],
                        },
                        "ProvisionedThroughput": {
                            "ReadCapacityUnits": 5,
                            "WriteCapacityUnits": 5,
                        },
                    }
                ],
                ProvisionedThroughput={
                    "ReadCapacityUnits": 5,
                    "WriteCapacityUnits": 5,
                },
            )
            break
        except ClientError as error:
            if error.response["Error"]["Code"] == "ResourceInUseException":
                break
            if attempt == 29:
                raise
        except BotoCoreError:
            if attempt == 29:
                raise
        time.sleep(1)
    seed_local_chats(client, table_name=settings.dynamodb_chat_table_name)


if __name__ == "__main__":
    main()
