import { execFileSync } from "node:child_process";
import { loadInfraSettings } from "../config/settings";

const settings = loadInfraSettings();
const account = execFileSync(
    "aws",
    ["sts", "get-caller-identity", "--query", "Account", "--output", "text"],
    { encoding: "utf8" },
).trim();

execFileSync(
    "pnpm",
    ["cdk", "bootstrap", `aws://${account}/${settings.region}`],
    { stdio: "inherit" },
);
