import { fetchAuthSession } from "aws-amplify/auth";

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
