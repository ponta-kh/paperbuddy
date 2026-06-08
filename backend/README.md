# PaperBuddy Backend

## Prerequisites

- Python 3.14 and uv
- An AWS profile with access to the target Bedrock Knowledge Base and model
- Model access enabled in the AWS region used by the Knowledge Base

The application uses boto3's standard AWS credential provider chain. Do not put
AWS access keys in `.env`.

## Local Configuration

Create the local environment file and replace the Bedrock identifiers:

```sh
cp .env.example .env
```

For an AWS SSO profile, authenticate before starting the backend:

```sh
aws sso login --profile your-profile
AWS_PROFILE=your-profile aws sts get-caller-identity
```

Set the same profile name in `.env`.

The default `CHAT_REPOSITORY_TYPE=in_memory` keeps local development
self-contained. To use the persistent DynamoDB repository, set:

```dotenv
CHAT_REPOSITORY_TYPE=dynamodb
DYNAMODB_CHAT_TABLE_NAME=your-chat-table-name
```

The DynamoDB table and `gsi1` key schema are defined in
`docs/backend/specification/integrations/dynamodb_chat_repository.md`.

## Run on the Host

```sh
uv sync
uv run uvicorn main:app --reload --env-file .env
```

## Run with Docker Compose

The Compose service mounts the host's `~/.aws` directory read-only so boto3 can
use the configured profile and AWS SSO cache. It overrides the container user
to root locally so AWS files with `0600` permissions remain readable. The
production Docker image still runs as a non-root user.

```sh
docker compose up --build
```

## Test the Bedrock Connection

Start the backend, then create a chat. This calls both Knowledge Base
`RetrieveAndGenerate` and Bedrock Runtime `Converse`.

```sh
curl --fail-with-body \
  -X POST http://localhost:8000/api/chats \
  -H 'Content-Type: application/json' \
  -H 'X-User-ID: 00000000-0000-0000-0000-000000000001' \
  -d '{"prompt":"このナレッジベースの内容を簡潔に説明してください"}'
```

Required permissions for the AWS identity include:

- `bedrock:RetrieveAndGenerate`
- `bedrock:InvokeModel`

The Bedrock Knowledge Base and model must be available in `AWS_REGION`.
