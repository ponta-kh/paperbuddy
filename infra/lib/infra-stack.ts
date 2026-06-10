import * as cdk from "aws-cdk-lib/core";
import type { Construct } from "constructs";
import { createBackend } from "./backend";
import { createDatabaseResources } from "./database";
import { createFrontendDelivery } from "./frontend-delivery";
import { createLlmResources, grantBackendBedrockAccess } from "./llm";
import { connectBackendToAwsServices, createNetwork } from "./network";

export interface InfraStackProps extends cdk.StackProps {
    readonly stageName: string;
    readonly frontendAssetPath?: string;
    readonly backendAssetPath?: string;
}

export class InfraStack extends cdk.Stack {
    constructor(scope: Construct, id: string, props: InfraStackProps) {
        super(scope, id, props);

        const database = createDatabaseResources(this, props.stageName);
        const llm = createLlmResources(this);
        const network = createNetwork(this);
        const backend = createBackend(this, {
            assetPath: props.backendAssetPath,
            llm,
            network,
            database,
        });
        grantBackendBedrockAccess(
            backend.backendService.taskDefinition.taskRole,
            llm,
        );
        connectBackendToAwsServices(
            this,
            network,
            backend.backendService.service,
        );
        const frontendDelivery = createFrontendDelivery(this, {
            assetPath: props.frontendAssetPath,
            backendLoadBalancer: backend.backendService.loadBalancer,
        });

        new cdk.CfnOutput(this, "ChatTableName", {
            value: database.chatTable.tableName,
        });
        new cdk.CfnOutput(this, "ChatTableArn", {
            value: database.chatTable.tableArn,
        });
        new cdk.CfnOutput(this, "LibraryTableName", {
            value: database.libraryTable.tableName,
        });
        new cdk.CfnOutput(this, "LibraryTableArn", {
            value: database.libraryTable.tableArn,
        });
        new cdk.CfnOutput(this, "FrontendBucketName", {
            value: frontendDelivery.frontendBucket.bucketName,
        });
        new cdk.CfnOutput(this, "RagSourceBucketName", {
            value: llm.ragSourceBucket.bucketName,
        });
        new cdk.CfnOutput(this, "RagSourceBucketArn", {
            value: llm.ragSourceBucket.bucketArn,
        });
        new cdk.CfnOutput(this, "DistributionDomainName", {
            value: frontendDelivery.distribution.distributionDomainName,
        });
    }
}
