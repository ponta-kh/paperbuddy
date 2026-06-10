const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";
const USER_ID = import.meta.env.VITE_USER_ID;

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
    if (!USER_ID) {
        throw new Error("VITE_USER_ID is not configured");
    }

    const response = await fetch(`${API_BASE_URL}/library/files`, {
        method: "GET",
        headers: {
            Accept: "application/json",
            "X-User-ID": USER_ID,
        },
        signal,
    });

    if (!response.ok) {
        throw new Error(`API request failed: ${response.status}`);
    }

    const result = (await response.json()) as ListIndexedFilesResponse;
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
