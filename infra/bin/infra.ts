#!/usr/bin/env node
import * as cdk from "aws-cdk-lib/core";
import { InfraStack } from "../lib/infra-stack";

const app = new cdk.App();
new InfraStack(app, "PaperBuddyDev", {
    stageName: "dev",
    env: {
        account: process.env.CDK_DEFAULT_ACCOUNT,
        region:
            process.env.AWS_REGION ??
            process.env.CDK_DEFAULT_REGION ??
            "ap-northeast-1",
    },
});
