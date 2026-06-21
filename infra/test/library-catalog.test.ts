import { describe, expect, test } from "vitest";
import {
    buildBatchWritePayload,
    buildCatalogItems,
    buildCatalogWriteRequests,
    parseExistingCatalogResponse,
    parseS3ObjectsResponse,
} from "../scripts/library-catalog";

describe("library catalog sync", () => {
    test("S3オブジェクトから分類別カタログ項目を生成する", () => {
        const items = buildCatalogItems([
            {
                key: "documents/IT/RAG Survey.pdf",
                lastModified: "2026-01-01T00:00:00.000Z",
            },
            {
                key: "documents/Finance/Report.PDF",
                lastModified: "2026-01-02T03:04:05.000Z",
            },
        ]);

        expect(items).toEqual([
            {
                sourceId: expect.stringMatching(
                    /^[0-9a-f]{8}-[0-9a-f]{4}-5[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/,
                ),
                s3Key: "documents/Finance/Report.PDF",
                paperTitle: "Report",
                category: "Finance",
                status: "uploaded",
                s3UploadedAt: "2026-01-02T03:04:05Z",
            },
            {
                sourceId: expect.stringMatching(
                    /^[0-9a-f]{8}-[0-9a-f]{4}-5[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/,
                ),
                s3Key: "documents/IT/RAG Survey.pdf",
                paperTitle: "RAG Survey",
                category: "IT",
                status: "uploaded",
                s3UploadedAt: "2026-01-01T00:00:00Z",
            },
        ]);
    });

    test("分類フォルダ外のPDFを拒否する", () => {
        expect(() =>
            buildCatalogItems([
                {
                    key: "documents/RAG Survey.pdf",
                    lastModified: "2026-01-01T00:00:00.000Z",
                },
            ]),
        ).toThrow("分類フォルダ配下ではないPDF");
    });

    test("現在のS3一覧を登録し、消えた既存項目を削除する", () => {
        const currentItems = buildCatalogItems([
            {
                key: "documents/IT/RAG Survey.pdf",
                lastModified: "2026-01-01T00:00:00.000Z",
            },
        ]);
        const existingItems = [
            {
                pk: "SOURCE#old",
                sk: "SOURCE",
                s3Key: "documents/old.pdf",
            },
        ];

        const requests = buildCatalogWriteRequests(currentItems, existingItems);

        expect(requests).toHaveLength(2);
        expect(requests[0].PutRequest?.Item.s3_key).toEqual({
            S: "documents/IT/RAG Survey.pdf",
        });
        expect(requests[0].PutRequest?.Item.category).toEqual({ S: "IT" });
        expect(requests[0].PutRequest?.Item.paper_title).toEqual({
            S: "RAG Survey",
        });
        expect(requests[0].PutRequest?.Item.rag_indexed_at).toBeUndefined();
        expect(requests[1]).toEqual({
            DeleteRequest: {
                Key: {
                    pk: { S: "SOURCE#old" },
                    sk: { S: "SOURCE" },
                },
            },
        });
    });

    test("AWS CLIレスポンスをDynamoDB登録ペイロードへ変換する", () => {
        const s3Objects = parseS3ObjectsResponse(
            JSON.stringify([
                {
                    Key: "documents/IT/RAG Survey.pdf",
                    LastModified: "2026-01-01T00:00:00.000Z",
                },
            ]),
        );
        const existingItems = parseExistingCatalogResponse(
            JSON.stringify([
                {
                    pk: { S: "SOURCE#old" },
                    sk: { S: "SOURCE" },
                    s3_key: { S: "documents/old.pdf" },
                },
            ]),
        );
        const requests = buildCatalogWriteRequests(
            buildCatalogItems(s3Objects),
            existingItems,
        );

        const payload = JSON.parse(
            buildBatchWritePayload("library-table", requests),
        );

        expect(payload).toHaveProperty("library-table");
        expect(payload["library-table"]).toHaveLength(2);
    });
});
