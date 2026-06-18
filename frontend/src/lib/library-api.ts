import { requestJson } from "@/lib/api-client";

export type IndexedFile = {
    id: string;
    s3Key: string;
    name: string;
    category: string;
    status: string;
    s3UploadedAt: string;
    ragIndexedAt: string | null;
};

type ListIndexedFilesResponse = {
    files: Array<{
        source_id: string;
        s3_key: string;
        name: string;
        category: string;
        status: string;
        s3_uploaded_at: string;
        rag_indexed_at: string | null;
    }>;
};

export async function getIndexedFiles(
    signal?: AbortSignal,
): Promise<IndexedFile[]> {
    const result = await requestJson<ListIndexedFilesResponse>(
        "/library/files",
        {
            method: "GET",
            signal,
        },
    );
    return result.files.map((file) => ({
        id: file.source_id,
        s3Key: file.s3_key,
        name: file.name,
        category: file.category,
        status: file.status,
        s3UploadedAt: file.s3_uploaded_at,
        ragIndexedAt: file.rag_indexed_at,
    }));
}
