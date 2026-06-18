import { execFileSync } from "node:child_process";
import { loadInfraSettings } from "../config/settings";

const settings = loadInfraSettings();

execFileSync(
    "aws",
    [
        "bedrock",
        "get-foundation-model-availability",
        "--region",
        settings.region,
        "--model-id",
        settings.bedrockModelArn.split("/").at(-1) ?? settings.bedrockModelArn,
    ],
    { stdio: "inherit" },
);
