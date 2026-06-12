import * as fs from "node:fs";
import * as path from "node:path";

export interface InfraSettings {
    readonly stackName: string;
    readonly region: string;
    readonly bedrockModelArn: string;
}

const ENV_FILE_PATH = path.join(__dirname, "../.env");

export function loadInfraSettings(): InfraSettings {
    const rawEntries = readDotEnvFile(ENV_FILE_PATH);
    const entries = new Map<string, string>(Object.entries(rawEntries));

    const stackName = required(entries, "STACK_NAME");
    const region = required(entries, "AWS_REGION");
    const bedrockModelArn = required(entries, "BEDROCK_MODEL_ARN");

    return {
        stackName,
        region,
        bedrockModelArn,
    };
}

function readDotEnvFile(filePath: string): Record<string, string> {
    if (!fs.existsSync(filePath)) {
        throw new Error(
            `infra設定ファイルが見つかりません: ${filePath}\n` +
                "infra/.env.example を infra/.env にコピーして値を設定してください。",
        );
    }

    const content = fs.readFileSync(filePath, "utf8");
    const result: Record<string, string> = {};

    for (const line of content.split(/\r?\n/)) {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith("#")) continue;

        const separatorIndex = trimmed.indexOf("=");
        if (separatorIndex <= 0) {
            continue;
        }

        const key = trimmed.slice(0, separatorIndex).trim();
        const value = unquote(trimmed.slice(separatorIndex + 1).trim());
        result[key] = value;
    }

    return result;
}

function required(entries: Map<string, string>, key: string): string {
    const value = entries.get(key);
    if (!value) {
        throw new Error(`infra設定の${key}が未設定です`);
    }
    return value;
}

function unquote(value: string): string {
    if (value.length < 2) return value;

    const first = value[0];
    const last = value.at(-1);
    if (first !== last || (first !== '"' && first !== "'")) {
        return value;
    }

    return value.slice(1, -1);
}
