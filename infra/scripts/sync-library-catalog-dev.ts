import { execFileSync } from "node:child_process";
import { existsSync, unlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { loadInfraSettings } from "../config/settings";
import {
    buildBatchWritePayload,
    buildCatalogItems,
    buildCatalogWriteRequests,
    chunkRequests,
    DATA_SOURCE_PREFIX,
    parseExistingCatalogResponse,
    parseS3ObjectsResponse,
} from "./library-catalog";

const BATCH_WRITE_LIMIT = 25;

const settings = loadInfraSettings();
const ragSourceBucketName = stackOutput("RagSourceBucketName");
const libraryTableName = stackOutput("LibraryTableName");
const s3Objects = parseS3ObjectsResponse(
    execAws([
        "s3api",
        "list-objects-v2",
        "--bucket",
        ragSourceBucketName,
        "--prefix",
        DATA_SOURCE_PREFIX,
        "--query",
        "Contents[].{Key: Key, LastModified: LastModified}",
        "--output",
        "json",
    ]),
);
const catalogItems = buildCatalogItems(s3Objects);
const existingItems = parseExistingCatalogResponse(
    execAws([
        "dynamodb",
        "scan",
        "--table-name",
        libraryTableName,
        "--projection-expression",
        "pk, sk, s3_key",
        "--output",
        "json",
        "--query",
        "Items",
    ]),
);
const writeRequests = buildCatalogWriteRequests(catalogItems, existingItems);

if (writeRequests.length === 0) {
    console.log("ライブラリカタログの同期対象はありません");
    process.exit(0);
}

for (const [index, chunk] of chunkRequests(
    writeRequests,
    BATCH_WRITE_LIMIT,
).entries()) {
    const payloadPath = join(
        tmpdir(),
        `paperbuddy-library-catalog-${process.pid}-${index}.json`,
    );
    try {
        writeFileSync(
            payloadPath,
            buildBatchWritePayload(libraryTableName, chunk),
        );
        const result = execAws([
            "dynamodb",
            "batch-write-item",
            "--request-items",
            `file://${payloadPath}`,
            "--output",
            "json",
        ]);
        assertNoUnprocessedItems(result);
    } finally {
        if (existsSync(payloadPath)) {
            unlinkSync(payloadPath);
        }
    }
}

console.log(
    [
        "ライブラリカタログを同期しました",
        `登録PDF: ${catalogItems.length}件`,
        `書き込みリクエスト: ${writeRequests.length}件`,
    ].join("\n"),
);

function stackOutput(outputKey: string): string {
    const value = execAws([
        "cloudformation",
        "describe-stacks",
        "--stack-name",
        settings.stackName,
        "--query",
        `Stacks[0].Outputs[?OutputKey=='${outputKey}'].OutputValue | [0]`,
        "--output",
        "text",
    ]).trim();

    if (!value || value === "None") {
        throw new Error(
            `CloudFormation Outputから${outputKey}を取得できませんでした`,
        );
    }
    return value;
}

function execAws(args: string[]): string {
    return execFileSync("aws", ["--region", settings.region, ...args], {
        encoding: "utf8",
    });
}

function assertNoUnprocessedItems(raw: string): void {
    const parsed = JSON.parse(raw) as unknown;
    if (!isRecord(parsed)) {
        throw new Error("DynamoDB BatchWriteItemのレスポンス形式が不正です");
    }
    const unprocessedItems = parsed.UnprocessedItems;
    if (!isRecord(unprocessedItems)) {
        return;
    }
    let unprocessedCount = 0;
    for (const value of Object.values(unprocessedItems)) {
        if (Array.isArray(value)) {
            unprocessedCount += value.length;
        }
    }
    if (unprocessedCount > 0) {
        throw new Error(
            `DynamoDB BatchWriteItemに未処理項目があります: ${unprocessedCount}件`,
        );
    }
}

function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null;
}
