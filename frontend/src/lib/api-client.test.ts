import { fetchAuthSession } from "aws-amplify/auth";
import { beforeEach, expect, test, vi } from "vitest";
import { ApiError, getApiHeaders, requestJson } from "./api-client";

vi.mock("aws-amplify/auth", () => ({
    fetchAuthSession: vi.fn(),
}));

beforeEach(() => {
    vi.mocked(fetchAuthSession).mockReset();
    vi.stubGlobal("fetch", vi.fn());
});

test("アクセストークンをBearerヘッダーとして返す", async () => {
    vi.mocked(fetchAuthSession).mockResolvedValue({
        tokens: {
            accessToken: {
                toString: () => "access-token",
            },
        },
    } as Awaited<ReturnType<typeof fetchAuthSession>>);

    await expect(getApiHeaders(true)).resolves.toEqual({
        Accept: "application/json",
        Authorization: "Bearer access-token",
        "Content-Type": "application/json",
    });
});

test("アクセストークンがない場合は失敗する", async () => {
    vi.mocked(fetchAuthSession).mockResolvedValue(
        {} as Awaited<ReturnType<typeof fetchAuthSession>>,
    );

    await expect(getApiHeaders()).rejects.toThrow(
        "アクセストークンを取得できませんでした",
    );
});

test("JSONリクエストを送信しレスポンスを返す", async () => {
    vi.mocked(fetchAuthSession).mockResolvedValue({
        tokens: {
            accessToken: {
                toString: () => "access-token",
            },
        },
    } as Awaited<ReturnType<typeof fetchAuthSession>>);
    vi.mocked(fetch).mockResolvedValue({
        ok: true,
        status: 200,
        json: vi.fn().mockResolvedValue({ hello: "world" }),
    } as unknown as Response);

    await expect(
        requestJson<{ hello: string }>("/hello", {
            method: "POST",
            body: { name: "paperbuddy" },
        }),
    ).resolves.toEqual({ hello: "world" });

    expect(fetch).toHaveBeenCalledWith(
        "/api/hello",
        expect.objectContaining({
            method: "POST",
            body: JSON.stringify({ name: "paperbuddy" }),
            headers: {
                Accept: "application/json",
                Authorization: "Bearer access-token",
                "Content-Type": "application/json",
            },
        }),
    );
});

test("204 No Content を空値として扱う", async () => {
    vi.mocked(fetchAuthSession).mockResolvedValue({
        tokens: {
            accessToken: {
                toString: () => "access-token",
            },
        },
    } as Awaited<ReturnType<typeof fetchAuthSession>>);
    vi.mocked(fetch).mockResolvedValue({
        ok: true,
        status: 204,
    } as unknown as Response);

    await expect(
        requestJson<void>("/hello", { method: "DELETE" }),
    ).resolves.toBeUndefined();
});

test("失敗レスポンスは例外にする", async () => {
    vi.mocked(fetchAuthSession).mockResolvedValue({
        tokens: {
            accessToken: {
                toString: () => "access-token",
            },
        },
    } as Awaited<ReturnType<typeof fetchAuthSession>>);
    vi.mocked(fetch).mockResolvedValue({
        ok: false,
        status: 409,
        json: vi.fn().mockResolvedValue({
            code: "chat_continuation_expired",
            message: "このチャットでは会話を継続できません",
        }),
    } as unknown as Response);

    const error = await requestJson<void>("/hello", { method: "GET" }).catch(
        (caught: unknown) => caught,
    );

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({
        status: 409,
        code: "chat_continuation_expired",
        message: "このチャットでは会話を継続できません",
    });
});

test("JSONでない失敗レスポンスでも型付き例外にする", async () => {
    vi.mocked(fetchAuthSession).mockResolvedValue({
        tokens: {
            accessToken: {
                toString: () => "access-token",
            },
        },
    } as Awaited<ReturnType<typeof fetchAuthSession>>);
    vi.mocked(fetch).mockResolvedValue({
        ok: false,
        status: 500,
        json: vi.fn().mockRejectedValue(new SyntaxError()),
    } as unknown as Response);

    await expect(
        requestJson<void>("/hello", { method: "GET" }),
    ).rejects.toMatchObject({
        status: 500,
        code: "api_request_failed",
        message: "API request failed: 500",
    });
});
