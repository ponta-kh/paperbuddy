const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";
const USER_ID = import.meta.env.VITE_USER_ID;

export type IndexedFile = {
    name: string;
};

type ListIndexedFilesResponse = {
    files: IndexedFile[];
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
    return result.files;
}
