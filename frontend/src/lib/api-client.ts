import { fetchAuthSession } from "aws-amplify/auth";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

export async function getApiHeaders(
    includeContentType = false,
): Promise<Record<string, string>> {
    const session = await fetchAuthSession();
    const accessToken = session.tokens?.accessToken;

    if (!accessToken) {
        throw new Error("アクセストークンを取得できませんでした");
    }

    return {
        Accept: "application/json",
        Authorization: `Bearer ${accessToken.toString()}`,
        ...(includeContentType ? { "Content-Type": "application/json" } : {}),
    };
}

type RequestJsonOptions = {
    method: "GET" | "POST" | "PATCH" | "DELETE";
    signal?: AbortSignal;
    body?: unknown;
};

export async function requestJson<TResponse>(
    path: string,
    { method, signal, body }: RequestJsonOptions,
): Promise<TResponse> {
    const response = await fetch(`${API_BASE_URL}${path}`, {
        method,
        headers: await getApiHeaders(body !== undefined),
        signal,
        ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
    });

    if (!response.ok) {
        throw new Error(`API request failed: ${response.status}`);
    }

    if (response.status === 204) {
        return undefined as TResponse;
    }

    return response.json() as Promise<TResponse>;
}
