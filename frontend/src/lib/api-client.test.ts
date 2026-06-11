import { fetchAuthSession } from "aws-amplify/auth";
import { beforeEach, expect, test, vi } from "vitest";
import { getApiHeaders } from "./api-client";

vi.mock("aws-amplify/auth", () => ({
    fetchAuthSession: vi.fn(),
}));

beforeEach(() => {
    vi.mocked(fetchAuthSession).mockReset();
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
