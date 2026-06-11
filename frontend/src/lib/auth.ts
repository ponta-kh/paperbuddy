import { Amplify } from "aws-amplify";

type AuthConfig = {
    userPoolId: string;
    userPoolClientId: string;
};

function getLocalAuthConfig(): AuthConfig | undefined {
    const userPoolId = import.meta.env.VITE_COGNITO_USER_POOL_ID;
    const userPoolClientId = import.meta.env.VITE_COGNITO_USER_POOL_CLIENT_ID;

    if (!userPoolId || !userPoolClientId) return undefined;
    return { userPoolId, userPoolClientId };
}

export async function configureAuth(): Promise<void> {
    let authConfig = getLocalAuthConfig();

    if (!authConfig) {
        const response = await fetch("/auth-config.json", {
            headers: { Accept: "application/json" },
        });
        if (!response.ok) {
            throw new Error("認証設定を取得できませんでした");
        }
        authConfig = (await response.json()) as AuthConfig;
    }

    Amplify.configure({
        Auth: {
            Cognito: {
                userPoolId: authConfig.userPoolId,
                userPoolClientId: authConfig.userPoolClientId,
            },
        },
    });
}
