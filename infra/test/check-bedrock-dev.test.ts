import { describe, expect, test } from "vitest";
import { buildBedrockModelCheckArgs } from "../scripts/check-bedrock-dev";

describe("buildBedrockModelCheckArgs", () => {
    test("cross-region inference profile IDはInference Profileとして確認する", () => {
        expect(
            buildBedrockModelCheckArgs(
                "ap-northeast-1",
                "apac.anthropic.claude-3-5-sonnet-20241022-v2:0",
            ),
        ).toEqual([
            "bedrock",
            "get-inference-profile",
            "--region",
            "ap-northeast-1",
            "--inference-profile-identifier",
            "apac.anthropic.claude-3-5-sonnet-20241022-v2:0",
        ]);
    });

    test("global inference profile IDはInference Profileとして確認する", () => {
        expect(
            buildBedrockModelCheckArgs(
                "ap-northeast-1",
                "global.anthropic.claude-sonnet-4-20250514-v1:0",
            ),
        ).toEqual([
            "bedrock",
            "get-inference-profile",
            "--region",
            "ap-northeast-1",
            "--inference-profile-identifier",
            "global.anthropic.claude-sonnet-4-20250514-v1:0",
        ]);
    });

    test("Inference Profile ARNはARNのまま確認する", () => {
        const inferenceProfileArn =
            "arn:aws:bedrock:ap-northeast-1:123456789012:inference-profile/example";

        expect(
            buildBedrockModelCheckArgs("ap-northeast-1", inferenceProfileArn),
        ).toEqual([
            "bedrock",
            "get-inference-profile",
            "--region",
            "ap-northeast-1",
            "--inference-profile-identifier",
            inferenceProfileArn,
        ]);
    });

    test("Foundation Model ARNはモデルIDを取り出して確認する", () => {
        expect(
            buildBedrockModelCheckArgs(
                "ap-northeast-1",
                "arn:aws:bedrock:ap-northeast-1::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0",
            ),
        ).toEqual([
            "bedrock",
            "get-foundation-model-availability",
            "--region",
            "ap-northeast-1",
            "--model-id",
            "anthropic.claude-3-5-sonnet-20241022-v2:0",
        ]);
    });

    test("Foundation Model IDはそのまま確認する", () => {
        expect(
            buildBedrockModelCheckArgs(
                "ap-northeast-1",
                "anthropic.claude-3-5-sonnet-20241022-v2:0",
            ),
        ).toEqual([
            "bedrock",
            "get-foundation-model-availability",
            "--region",
            "ap-northeast-1",
            "--model-id",
            "anthropic.claude-3-5-sonnet-20241022-v2:0",
        ]);
    });
});
