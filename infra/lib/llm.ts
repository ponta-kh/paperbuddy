import * as iam from "aws-cdk-lib/aws-iam";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as cdk from "aws-cdk-lib/core";
import type { Construct } from "constructs";

export interface LlmResources {
    readonly knowledgeBaseId: cdk.CfnParameter;
    readonly modelArn: cdk.CfnParameter;
    readonly ragSourceBucket: s3.Bucket;
}

export function createLlmResources(scope: Construct): LlmResources {
    const ragSourceBucket = new s3.Bucket(scope, "RagSourceBucket", {
        blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
        encryption: s3.BucketEncryption.S3_MANAGED,
        enforceSSL: true,
        versioned: true,
        removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    const knowledgeBaseId = new cdk.CfnParameter(
        scope,
        "BedrockKnowledgeBaseId",
        {
            type: "String",
            description: "Bedrock Knowledge Base ID used by the backend",
        },
    );
    const modelArn = new cdk.CfnParameter(scope, "BedrockModelArn", {
        type: "String",
        description: "Bedrock model ARN used by the backend",
    });

    return {
        knowledgeBaseId,
        modelArn,
        ragSourceBucket,
    };
}

export function grantBackendBedrockAccess(
    taskRole: iam.IRole,
    llm: LlmResources,
): void {
    taskRole.addToPrincipalPolicy(
        new iam.PolicyStatement({
            actions: ["bedrock:RetrieveAndGenerate"],
            resources: ["*"],
        }),
    );
    taskRole.addToPrincipalPolicy(
        new iam.PolicyStatement({
            actions: ["bedrock:InvokeModel"],
            resources: [llm.modelArn.valueAsString],
        }),
    );
}
