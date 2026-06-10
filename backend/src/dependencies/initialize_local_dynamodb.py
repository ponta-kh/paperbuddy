import os
import time

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from src.dependencies.local_chat_seed import seed_local_chats


def main() -> None:
    endpoint_url = os.environ["DYNAMODB_ENDPOINT_URL"]
    region = os.environ["AWS_REGION"]
    table_name = os.environ["DYNAMODB_CHAT_TABLE_NAME"]
    client = boto3.client("dynamodb", region_name=region, endpoint_url=endpoint_url)

    for attempt in range(30):
        try:
            client.create_table(
                TableName=table_name,
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
    seed_local_chats(client, table_name=table_name)


if __name__ == "__main__":
    main()
