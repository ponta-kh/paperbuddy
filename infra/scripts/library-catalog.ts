import { createHash } from "node:crypto";

export const DATA_SOURCE_PREFIX = "documents/";
const SOURCE_ID_NAMESPACE = "4eb6c0f8-35af-5e8f-9b9d-77b53440156d";
const CATALOG_STATUS = "uploaded";

export interface S3ObjectSummary {
    readonly key: string;
    readonly lastModified: string;
}

export interface LibraryCatalogItem {
    readonly sourceId: string;
    readonly s3Key: string;
    readonly fileName: string;
    readonly category: string;
    readonly status: string;
    readonly s3UploadedAt: string;
}

export interface ExistingCatalogItem {
    readonly pk: string;
    readonly sk: string;
    readonly s3Key: string;
}

interface DynamoDbWriteRequest {
    readonly PutRequest?: {
        readonly Item: Record<string, Record<string, string>>;
    };
    readonly DeleteRequest?: {
        readonly Key: Record<string, Record<string, string>>;
    };
}

export function buildCatalogItems(
    objects: readonly S3ObjectSummary[],
): LibraryCatalogItem[] {
    return objects
        .filter((object) => isPdfKey(object.key))
        .map((object) => {
            const relativeKey = object.key.slice(DATA_SOURCE_PREFIX.length);
            const segments = relativeKey.split("/").filter(Boolean);
            const fileName = segments.at(-1);
            const category = segments.at(0);

            if (!fileName || !category || segments.length < 2) {
                throw new Error(
                    `分類フォルダ配下ではないPDFが見つかりました: ${object.key}`,
                );
            }

            return {
                sourceId: uuidV5(object.key, SOURCE_ID_NAMESPACE),
                s3Key: object.key,
                fileName,
                category,
                status: CATALOG_STATUS,
                s3UploadedAt: formatDynamoDbDateTime(object.lastModified),
            };
        })
        .sort((left, right) => left.s3Key.localeCompare(right.s3Key));
}

export function buildCatalogWriteRequests(
    currentItems: readonly LibraryCatalogItem[],
    existingItems: readonly ExistingCatalogItem[],
): DynamoDbWriteRequest[] {
    const currentKeys = new Set(currentItems.map((item) => item.s3Key));
    const putRequests = currentItems.map((item) => ({
        PutRequest: {
            Item: {
                pk: { S: catalogPk(item.sourceId) },
                sk: { S: "SOURCE" },
                source_id: { S: item.sourceId },
                s3_key: { S: item.s3Key },
                file_name: { S: item.fileName },
                category: { S: item.category },
                status: { S: item.status },
                s3_uploaded_at: { S: item.s3UploadedAt },
            },
        },
    }));
    const deleteRequests = existingItems
        .filter((item) => !currentKeys.has(item.s3Key))
        .map((item) => ({
            DeleteRequest: {
                Key: {
                    pk: { S: item.pk },
                    sk: { S: item.sk },
                },
            },
        }));

    return [...putRequests, ...deleteRequests];
}

export function parseS3ObjectsResponse(raw: string): S3ObjectSummary[] {
    const parsed = JSON.parse(raw) as unknown;
    if (parsed === null) {
        return [];
    }
    if (!Array.isArray(parsed)) {
        throw new Error("S3オブジェクト一覧の形式が不正です");
    }

    return parsed.map((item) => {
        if (!isRecord(item)) {
            throw new Error("S3オブジェクト一覧の要素形式が不正です");
        }
        const key = item.Key;
        const lastModified = item.LastModified;
        if (typeof key !== "string" || typeof lastModified !== "string") {
            throw new Error("S3オブジェクト一覧に必要な属性がありません");
        }
        return { key, lastModified };
    });
}

export function parseExistingCatalogResponse(
    raw: string,
): ExistingCatalogItem[] {
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) {
        throw new Error("ライブラリカタログ一覧の形式が不正です");
    }

    return parsed.map((item) => {
        if (!isRecord(item)) {
            throw new Error("ライブラリカタログ一覧の要素形式が不正です");
        }
        const pk = item.pk;
        const sk = item.sk;
        const s3Key = item.s3_key;
        if (
            !isDynamoDbString(pk) ||
            !isDynamoDbString(sk) ||
            !isDynamoDbString(s3Key)
        ) {
            throw new Error("ライブラリカタログ一覧に必要な属性がありません");
        }
        return { pk: pk.S, sk: sk.S, s3Key: s3Key.S };
    });
}

export function buildBatchWritePayload(
    tableName: string,
    requests: readonly DynamoDbWriteRequest[],
): string {
    return JSON.stringify({
        [tableName]: requests,
    });
}

export function chunkRequests<T>(items: readonly T[], size: number): T[][] {
    const chunks: T[][] = [];
    for (let index = 0; index < items.length; index += size) {
        chunks.push(items.slice(index, index + size));
    }
    return chunks;
}

function isPdfKey(key: string): boolean {
    return key.startsWith(DATA_SOURCE_PREFIX) && /\.pdf$/i.test(key);
}

function formatDynamoDbDateTime(value: string): string {
    return new Date(value).toISOString().replace(".000Z", "Z");
}

function catalogPk(sourceId: string): string {
    return `SOURCE#${sourceId}`;
}

function uuidV5(name: string, namespace: string): string {
    const namespaceBytes = uuidToBytes(namespace);
    const nameBytes = Buffer.from(name, "utf8");
    const hash = createHash("sha1")
        .update(Buffer.concat([namespaceBytes, nameBytes]))
        .digest();

    hash[6] = (hash[6] & 0x0f) | 0x50;
    hash[8] = (hash[8] & 0x3f) | 0x80;

    return bytesToUuid(hash.subarray(0, 16));
}

function uuidToBytes(uuid: string): Buffer {
    return Buffer.from(uuid.replace(/-/g, ""), "hex");
}

function bytesToUuid(bytes: Buffer): string {
    const hex = bytes.toString("hex");
    return [
        hex.slice(0, 8),
        hex.slice(8, 12),
        hex.slice(12, 16),
        hex.slice(16, 20),
        hex.slice(20, 32),
    ].join("-");
}

function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null;
}

function isDynamoDbString(value: unknown): value is {
    readonly S: string;
} {
    return isRecord(value) && typeof value.S === "string";
}
