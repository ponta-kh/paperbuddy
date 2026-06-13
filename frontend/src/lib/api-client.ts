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

type ApiErrorResponse = {
    code?: unknown;
    message?: unknown;
};

export class ApiError extends Error {
    readonly status: number;
    readonly code: string;

    constructor(status: number, code: string, message: string) {
        super(message);
        this.name = "ApiError";
        this.status = status;
        this.code = code;
    }
}

async function createApiError(response: Response): Promise<ApiError> {
    let body: ApiErrorResponse = {};
    try {
        body = (await response.json()) as ApiErrorResponse;
    } catch {
        // JSONでないエラーレスポンスでもHTTPステータスは保持する。
    }

    const code =
        typeof body.code === "string" ? body.code : "api_request_failed";
    const message =
        typeof body.message === "string"
            ? body.message
            : `API request failed: ${response.status}`;
    return new ApiError(response.status, code, message);
}

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
        throw await createApiError(response);
    }

    if (response.status === 204) {
        return undefined as TResponse;
    }

    return response.json() as Promise<TResponse>;
}
