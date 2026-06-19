import { execFileSync } from "node:child_process";
import { loadInfraSettings } from "../config/settings";

export function buildBedrockModelCheckArgs(
    region: string,
    modelIdentifier: string,
): string[] {
    if (isInferenceProfileIdentifier(modelIdentifier)) {
        return [
            "bedrock",
            "get-inference-profile",
            "--region",
            region,
            "--inference-profile-identifier",
            modelIdentifier,
        ];
    }

    return [
        "bedrock",
        "get-foundation-model-availability",
        "--region",
        region,
        "--model-id",
        foundationModelId(modelIdentifier),
    ];
}

function isInferenceProfileIdentifier(modelIdentifier: string): boolean {
    if (
        modelIdentifier.includes(":inference-profile/") ||
        modelIdentifier.includes(":application-inference-profile/")
    ) {
        return true;
    }

    return /^(af|ap|apac|ca|eu|global|me|sa|us)\./.test(modelIdentifier);
}

function foundationModelId(modelIdentifier: string): string {
    return modelIdentifier.split("/").at(-1) ?? modelIdentifier;
}

if (require.main === module) {
    const settings = loadInfraSettings();

    execFileSync(
        "aws",
        buildBedrockModelCheckArgs(
            settings.region,
            settings.bedrockGenerationModelIdentifier,
        ),
        { stdio: "inherit" },
    );
}
