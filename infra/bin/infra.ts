#!/usr/bin/env node
import * as cdk from "aws-cdk-lib/core";
import { loadInfraSettings } from "../config/settings";
import { InfraStack } from "../lib/infra-stack";

const settings = loadInfraSettings();
const app = new cdk.App();
new InfraStack(app, settings.stackName, {
    stageName: "dev",
    bedrockModelArn: settings.bedrockModelArn,
    env: {
        account: process.env.CDK_DEFAULT_ACCOUNT,
        region: settings.region,
    },
});
